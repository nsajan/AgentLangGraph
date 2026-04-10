"""ReAct pattern: single agent with tools using LangGraph's create_react_agent."""

from __future__ import annotations

from langgraph.prebuilt import create_react_agent

from src.agent_builder.llm import create_llm
from src.agent_builder.schemas import AgentConfig
from src.agent_builder.tools import resolve_tools


def build_react_agent(config: AgentConfig, *, checkpointer=None):
    """Build a ReAct agent using LangGraph's built-in implementation.

    This is the most common pattern: an LLM that can call tools in a loop
    until it has a final answer.
    """
    if not config.agent:
        raise ValueError("ReAct pattern requires 'agent' config")

    llm = create_llm(model=config.agent.model)
    tools = resolve_tools(config.agent.tools)

    graph = create_react_agent(
        model=llm,
        tools=tools,
        prompt=config.agent.system_prompt,
        checkpointer=checkpointer,
    )

    return graph
