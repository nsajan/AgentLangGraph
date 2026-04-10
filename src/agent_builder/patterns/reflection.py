"""Reflection pattern: generator creates → critic reviews → loop until good."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from src.agent_builder.llm import create_llm
from src.agent_builder.schemas import AgentConfig


class ReflectionState(BaseModel):
    """State for the reflection loop."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    draft: str = ""
    critique: str = ""
    iteration: int = 0
    is_approved: bool = False


def build_reflection_agent(config: AgentConfig, *, checkpointer=None):
    """Build a Reflection agent.

    Flow: user query → generator (draft) → critic (review) → loop or finish
    """
    if not config.generator or not config.critic:
        raise ValueError("Reflection pattern requires 'generator' and 'critic' configs")

    gen_llm = create_llm(model=config.generator.model)
    critic_llm = create_llm(model=config.critic.model)
    max_iter = config.max_iterations

    gen_prompt = config.generator.system_prompt
    critic_prompt = config.critic.system_prompt

    async def generate_node(state: ReflectionState):
        """Generate or revise the draft."""
        messages = [SystemMessage(content=gen_prompt)]

        if state.iteration == 0:
            # First pass — use original user message
            messages.extend(state.messages)
        else:
            # Revision — include the critique
            messages.extend(state.messages)
            messages.append(HumanMessage(content=(
                f"Your previous draft:\n{state.draft}\n\n"
                f"Critique received:\n{state.critique}\n\n"
                "Please revise your response addressing the critique."
            )))

        response = await gen_llm.ainvoke(messages)
        return {
            "draft": response.content,
            "iteration": state.iteration + 1,
        }

    async def critique_node(state: ReflectionState):
        """Review the draft and decide if it's good enough."""
        messages = [
            SystemMessage(content=(
                f"{critic_prompt}\n\n"
                "Review the following draft. If it's good enough, respond with EXACTLY "
                "'APPROVED' as the first word. Otherwise, provide specific, actionable feedback."
            )),
            *state.messages[:1],  # original request
            HumanMessage(content=f"Draft to review:\n\n{state.draft}"),
        ]
        response = await critic_llm.ainvoke(messages)
        approved = response.content.strip().upper().startswith("APPROVED")

        return {
            "critique": response.content,
            "is_approved": approved,
        }

    def should_continue(state: ReflectionState):
        if state.is_approved or state.iteration >= max_iter:
            return "finalize"
        return "generate"

    async def finalize_node(state: ReflectionState):
        """Emit the final approved draft as the AI response."""
        return {
            "messages": [AIMessage(content=state.draft)],
        }

    # --- Build graph ---
    graph = StateGraph(ReflectionState)
    graph.add_node("generate", generate_node)
    graph.add_node("critique", critique_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "critique")
    graph.add_conditional_edges("critique", should_continue)
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer)
