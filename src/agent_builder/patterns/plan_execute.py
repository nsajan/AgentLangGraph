"""Plan & Execute pattern: a planner creates structured steps, an executor runs them."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.agent_builder.llm import create_llm
from src.agent_builder.schemas import AgentConfig
from src.agent_builder.tools import resolve_tools


class PlanExecuteState(BaseModel):
    """State that carries the plan between planner and executor."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    plan: list[str] = Field(default_factory=list)
    current_step: int = 0
    step_results: list[str] = Field(default_factory=list)
    final_answer: str = ""


def build_plan_execute_agent(config: AgentConfig, *, checkpointer=None):
    """Build a Plan & Execute agent.

    Flow: user query → planner (creates steps) → executor (runs each step with tools) → synthesize
    """
    if not config.planner or not config.executor:
        raise ValueError("Plan & Execute pattern requires 'planner' and 'executor' configs")

    planner_llm = create_llm(model=config.planner.model)
    executor_llm = create_llm(model=config.executor.model)
    executor_tools = resolve_tools(config.executor.tools)

    # Build executor as a react sub-agent
    executor_react = create_react_agent(
        model=executor_llm,
        tools=executor_tools,
        prompt=config.executor.system_prompt,
    ) if executor_tools else None

    planner_prompt = config.planner.system_prompt

    # --- Node functions ---

    async def plan_node(state: PlanExecuteState):
        """Generate a numbered plan from the user's request."""
        messages = [
            SystemMessage(content=(
                f"{planner_prompt}\n\n"
                "Given the user's request, create a numbered plan of steps to accomplish it. "
                "Output ONLY the plan as a numbered list, one step per line. "
                "Keep it concise — 2 to 5 steps maximum."
            )),
            *state.messages,
        ]
        response = await planner_llm.ainvoke(messages)

        # Parse plan from response
        lines = [
            line.strip().lstrip("0123456789.)- ").strip()
            for line in response.content.strip().split("\n")
            if line.strip() and any(c.isalpha() for c in line)
        ]

        return {
            "plan": lines if lines else [response.content],
            "current_step": 0,
            "step_results": [],
            "messages": [response],
        }

    async def execute_node(state: PlanExecuteState):
        """Execute the current step."""
        if state.current_step >= len(state.plan):
            return {}

        step = state.plan[state.current_step]
        step_msg = f"Execute this step: {step}"

        if executor_react:
            result = await executor_react.ainvoke(
                {"messages": [HumanMessage(content=step_msg)]}
            )
            last = result["messages"][-1]
            step_result = last.content if hasattr(last, "content") else str(last)
        else:
            messages = [
                SystemMessage(content=config.executor.system_prompt),
                HumanMessage(content=step_msg),
            ]
            response = await executor_llm.ainvoke(messages)
            step_result = response.content

        return {
            "step_results": [*state.step_results, step_result],
            "current_step": state.current_step + 1,
        }

    def should_continue(state: PlanExecuteState):
        """Check if there are more steps to execute."""
        if state.current_step < len(state.plan):
            return "execute"
        return "synthesize"

    async def synthesize_node(state: PlanExecuteState):
        """Combine all step results into a final answer."""
        summary_parts = []
        for i, (step, result) in enumerate(zip(state.plan, state.step_results)):
            summary_parts.append(f"Step {i+1}: {step}\nResult: {result}")

        messages = [
            SystemMessage(content=(
                "You executed a plan step by step. Synthesize the results into a clear, "
                "complete final answer for the user. Be concise but thorough."
            )),
            *state.messages[:1],  # original user query
            HumanMessage(content="Step results:\n\n" + "\n\n".join(summary_parts)),
        ]
        response = await planner_llm.ainvoke(messages)

        return {
            "final_answer": response.content,
            "messages": [AIMessage(content=response.content)],
        }

    # --- Build graph ---
    graph = StateGraph(PlanExecuteState)
    graph.add_node("planner", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "execute")
    graph.add_conditional_edges("execute", should_continue)
    graph.add_edge("synthesize", END)

    return graph.compile(checkpointer=checkpointer)
