"""Supervisor pattern: a router agent delegates to specialized worker agents."""

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


class SupervisorState(BaseModel):
    """State for the supervisor multi-agent system."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    next_worker: str = ""
    worker_results: dict[str, str] = Field(default_factory=dict)
    is_complete: bool = False


def build_supervisor_agent(config: AgentConfig, *, checkpointer=None):
    """Build a Supervisor agent.

    Flow: user query → supervisor routes to workers → workers report back → supervisor decides next or finishes
    """
    if not config.supervisor or not config.workers:
        raise ValueError("Supervisor pattern requires 'supervisor' and 'workers' configs")

    sup_llm = create_llm(model=config.supervisor.model)
    sup_prompt = config.supervisor.system_prompt

    worker_names = [w.name for w in config.workers]

    # Build worker sub-agents
    worker_agents = {}
    for w in config.workers:
        w_llm = create_llm(model=w.model)
        w_tools = resolve_tools(w.tools)
        if w_tools:
            worker_agents[w.name] = create_react_agent(
                model=w_llm, tools=w_tools, prompt=w.system_prompt,
            )
        else:
            # Simple LLM worker (no tools)
            worker_agents[w.name] = {"llm": w_llm, "prompt": w.system_prompt}

    # --- Node functions ---

    async def supervisor_node(state: SupervisorState):
        """Decide which worker to route to, or finish."""
        worker_list = ", ".join(worker_names)
        results_summary = ""
        if state.worker_results:
            parts = [f"- {k}: {v[:200]}" for k, v in state.worker_results.items()]
            results_summary = "\n\nResults from workers so far:\n" + "\n".join(parts)

        messages = [
            SystemMessage(content=(
                f"{sup_prompt}\n\n"
                f"You are a supervisor managing these workers: {worker_list}.\n"
                f"Based on the user's request, decide which worker to delegate to next.\n"
                f"Respond with EXACTLY one of: {worker_list}, or FINISH if the task is complete."
                f"{results_summary}"
            )),
            *state.messages,
        ]

        response = await sup_llm.ainvoke(messages)
        text = response.content.strip().upper()

        if "FINISH" in text:
            return {"is_complete": True, "next_worker": ""}

        # Find which worker was mentioned
        chosen = None
        for name in worker_names:
            if name.upper() in text:
                chosen = name
                break
        if not chosen:
            chosen = worker_names[0]  # fallback

        return {"next_worker": chosen}

    def route_to_worker(state: SupervisorState):
        if state.is_complete:
            return "synthesize"
        return f"worker_{state.next_worker}"

    async def make_worker_node(worker_name, worker):
        async def worker_node(state: SupervisorState):
            last_user = None
            for m in reversed(state.messages):
                if isinstance(m, HumanMessage):
                    last_user = m.content
                    break
            task = last_user or "Complete the assigned task."

            if isinstance(worker, dict):
                # Simple LLM worker
                messages = [
                    SystemMessage(content=worker["prompt"]),
                    HumanMessage(content=task),
                ]
                response = await worker["llm"].ainvoke(messages)
                result = response.content
            else:
                # React sub-agent
                response = await worker.ainvoke(
                    {"messages": [HumanMessage(content=task)]}
                )
                last = response["messages"][-1]
                result = last.content if hasattr(last, "content") else str(last)

            return {
                "worker_results": {**state.worker_results, worker_name: result},
            }
        return worker_node

    async def synthesize_node(state: SupervisorState):
        """Combine worker results into a final answer."""
        parts = [f"**{k}**:\n{v}" for k, v in state.worker_results.items()]
        combined = "\n\n".join(parts)

        messages = [
            SystemMessage(content=(
                "You are synthesizing results from specialized workers. "
                "Create a clear, unified final answer for the user."
            )),
            *state.messages[:1],
            HumanMessage(content=f"Worker results:\n\n{combined}"),
        ]
        response = await sup_llm.ainvoke(messages)
        return {"messages": [AIMessage(content=response.content)]}

    # --- Build graph ---
    graph = StateGraph(SupervisorState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("synthesize", synthesize_node)

    # Add worker nodes
    import asyncio
    for w in config.workers:
        node_name = f"worker_{w.name}"
        worker = worker_agents[w.name]

        # Create sync wrapper to build the async worker node
        async def _make(wn=w.name, wa=worker):
            return await make_worker_node(wn, wa)

        worker_fn = asyncio.get_event_loop().run_until_complete(_make()) if False else None

        # Use a factory to capture the closure properly
        def create_worker_fn(wname, wagent):
            async def fn(state: SupervisorState):
                last_user = None
                for m in reversed(state.messages):
                    if isinstance(m, HumanMessage):
                        last_user = m.content
                        break
                task = last_user or "Complete the assigned task."

                if isinstance(wagent, dict):
                    msgs = [SystemMessage(content=wagent["prompt"]), HumanMessage(content=task)]
                    response = await wagent["llm"].ainvoke(msgs)
                    result = response.content
                else:
                    response = await wagent.ainvoke({"messages": [HumanMessage(content=task)]})
                    last = response["messages"][-1]
                    result = last.content if hasattr(last, "content") else str(last)

                return {"worker_results": {**state.worker_results, wname: result}}
            return fn

        graph.add_node(node_name, create_worker_fn(w.name, worker_agents[w.name]))
        graph.add_edge(node_name, "supervisor")

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges("supervisor", route_to_worker)
    graph.add_edge("synthesize", END)

    return graph.compile(checkpointer=checkpointer)
