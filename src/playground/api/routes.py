"""API routes — sessions, chat (with streaming), presets, validation, export."""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.agent_builder.builder import AgentBuilder
from src.agent_builder.schemas import AgentConfig
from src.agents.presets import PRESETS

router = APIRouter()

# In-memory session store
_sessions: dict[str, dict[str, Any]] = {}


# --- Request / Response models ---

class CreateSessionRequest(BaseModel):
    config: AgentConfig | None = None
    preset: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    agent_name: str
    pattern: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    history: list[dict]
    steps: list[dict]


# --- Presets ---

@router.get("/presets")
async def list_presets():
    return {name: cfg.model_dump() for name, cfg in PRESETS.items()}


@router.get("/presets/{name}")
async def get_preset(name: str):
    if name not in PRESETS:
        raise HTTPException(404, f"Preset '{name}' not found")
    return PRESETS[name].model_dump()


# --- Sessions ---

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    if req.preset:
        if req.preset not in PRESETS:
            raise HTTPException(404, f"Preset '{req.preset}' not found")
        config = PRESETS[req.preset]
    elif req.config:
        config = req.config
    else:
        raise HTTPException(400, "Provide either 'config' or 'preset'")

    # Validate
    builder = AgentBuilder(config)
    errors = builder.validate()
    if errors:
        raise HTTPException(422, detail="; ".join(errors))

    # Build
    graph = builder.build(use_checkpointer=True)
    session_id = str(uuid.uuid4())[:8]

    _sessions[session_id] = {
        "graph": graph,
        "config": config,
        "history": [],
        "thread_id": session_id,
    }

    return CreateSessionResponse(
        session_id=session_id,
        agent_name=config.name,
        pattern=config.pattern.value,
    )


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, req: ChatRequest):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    graph = session["graph"]
    history = session["history"]

    history.append({"role": "user", "content": req.message})

    # Invoke with thread_id for checkpointing
    invoke_config = {"configurable": {"thread_id": session["thread_id"]}}
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=invoke_config,
    )

    # Extract the final AI message
    response_text = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            response_text = msg.content
            break

    if not response_text:
        response_text = str(result.get("messages", ["No response"])[-1])

    history.append({"role": "assistant", "content": response_text})

    # Collect step info for the UI
    steps = []
    for msg in result["messages"]:
        step = {"type": type(msg).__name__, "content": ""}
        if hasattr(msg, "content"):
            step["content"] = msg.content[:500] if msg.content else ""
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            step["tool_calls"] = [
                {"name": tc["name"], "args": tc.get("args", {})}
                for tc in msg.tool_calls
            ]
        steps.append(step)

    return ChatResponse(response=response_text, history=history, steps=steps)


@router.post("/sessions/{session_id}/chat/stream")
async def chat_stream(session_id: str, req: ChatRequest):
    """Stream agent responses via SSE."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")

    graph = session["graph"]
    history = session["history"]
    history.append({"role": "user", "content": req.message})
    invoke_config = {"configurable": {"thread_id": session["thread_id"]}}

    async def event_generator():
        final_response = ""
        try:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=req.message)]},
                config=invoke_config,
                version="v2",
            ):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield {"event": "token", "data": json.dumps({"token": chunk.content})}

                elif kind == "on_chat_model_start":
                    node = event.get("metadata", {}).get("langgraph_node", "")
                    yield {"event": "node_start", "data": json.dumps({"node": node})}

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    yield {"event": "tool_call", "data": json.dumps({"tool": tool_name})}

                elif kind == "on_tool_end":
                    output = event.get("data", {}).get("output", "")
                    if hasattr(output, "content"):
                        output = output.content
                    yield {"event": "tool_result", "data": json.dumps({"result": str(output)[:500]})}

            # Get final state
            state = await graph.aget_state(invoke_config)
            for msg in reversed(state.values.get("messages", [])):
                if isinstance(msg, AIMessage) and msg.content:
                    final_response = msg.content
                    break

            history.append({"role": "assistant", "content": final_response})
            yield {"event": "done", "data": json.dumps({"response": final_response})}

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return {
        "session_id": session_id,
        "agent_name": session["config"].name,
        "pattern": session["config"].pattern.value,
        "config": session["config"].model_dump(),
        "history": session["history"],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"deleted": session_id}


# --- Validation ---

@router.post("/validate")
async def validate_config(config: AgentConfig):
    builder = AgentBuilder(config)
    errors = builder.validate()
    return {"valid": len(errors) == 0, "errors": errors}


# --- Export Python code ---

@router.post("/export/python")
async def export_python(config: AgentConfig):
    """Generate a standalone Python script from an agent config."""
    code = _generate_python(config)
    return {"code": code}


def _generate_python(config: AgentConfig) -> str:
    """Generate runnable Python code for the given config."""
    lines = [
        '"""Auto-generated agent: {name}"""'.format(name=config.name),
        "",
        "from dotenv import load_dotenv",
        "load_dotenv()",
        "",
    ]

    p = config.pattern

    if p.value == "react":
        agent = config.agent
        tools_imports = []
        tool_names = [t.name for t in agent.tools] if agent else []

        lines.extend([
            "from langchain_anthropic import ChatAnthropic",
            "from langgraph.prebuilt import create_react_agent",
        ])

        if tool_names:
            lines.append("from src.agent_builder.tools import " + ", ".join(tool_names))

        lines.extend([
            "",
            f'llm = ChatAnthropic(model="{agent.model}", temperature=0)',
            "",
            f'agent = create_react_agent(',
            f'    model=llm,',
            f'    tools=[{", ".join(tool_names)}],',
            f'    prompt="""{agent.system_prompt}""",',
            f')',
            "",
        ])

    elif p.value == "plan_execute":
        lines.extend([
            "from src.agent_builder.patterns.plan_execute import build_plan_execute_agent",
            "from src.agent_builder.schemas import AgentConfig, AgentNodeConfig, PatternType, ToolConfig",
            "",
            "config = AgentConfig(",
            f'    name="{config.name}",',
            f'    pattern=PatternType.PLAN_EXECUTE,',
            f'    planner=AgentNodeConfig(',
            f'        name="{config.planner.name}",',
            f'        system_prompt="""{config.planner.system_prompt}""",',
            f'        model="{config.planner.model}",',
            f'    ),',
            f'    executor=AgentNodeConfig(',
            f'        name="{config.executor.name}",',
            f'        system_prompt="""{config.executor.system_prompt}""",',
            f'        model="{config.executor.model}",',
        ])
        if config.executor.tools:
            tools_str = ", ".join(f'ToolConfig(name="{t.name}")' for t in config.executor.tools)
            lines.append(f'        tools=[{tools_str}],')
        lines.extend([
            f'    ),',
            f')',
            "",
            "agent = build_plan_execute_agent(config)",
            "",
        ])

    elif p.value == "reflection":
        lines.extend([
            "from src.agent_builder.patterns.reflection import build_reflection_agent",
            "from src.agent_builder.schemas import AgentConfig, AgentNodeConfig, PatternType",
            "",
            "config = AgentConfig(",
            f'    name="{config.name}",',
            f'    pattern=PatternType.REFLECTION,',
            f'    max_iterations={config.max_iterations},',
            f'    generator=AgentNodeConfig(',
            f'        name="{config.generator.name}",',
            f'        system_prompt="""{config.generator.system_prompt}""",',
            f'        model="{config.generator.model}",',
            f'    ),',
            f'    critic=AgentNodeConfig(',
            f'        name="{config.critic.name}",',
            f'        system_prompt="""{config.critic.system_prompt}""",',
            f'        model="{config.critic.model}",',
            f'    ),',
            f')',
            "",
            "agent = build_reflection_agent(config)",
            "",
        ])

    elif p.value == "supervisor":
        lines.extend([
            "from src.agent_builder.patterns.supervisor import build_supervisor_agent",
            "from src.agent_builder.schemas import AgentConfig, AgentNodeConfig, PatternType, ToolConfig",
            "",
            "config = AgentConfig(",
            f'    name="{config.name}",',
            f'    pattern=PatternType.SUPERVISOR,',
            f'    supervisor=AgentNodeConfig(',
            f'        name="{config.supervisor.name}",',
            f'        system_prompt="""{config.supervisor.system_prompt}""",',
            f'        model="{config.supervisor.model}",',
            f'    ),',
            "    workers=[",
        ])
        for w in config.workers:
            lines.append(f'        AgentNodeConfig(')
            lines.append(f'            name="{w.name}",')
            lines.append(f'            system_prompt="""{w.system_prompt}""",')
            lines.append(f'            model="{w.model}",')
            if w.tools:
                tools_str = ", ".join(f'ToolConfig(name="{t.name}")' for t in w.tools)
                lines.append(f'            tools=[{tools_str}],')
            lines.append(f'        ),')
        lines.extend([
            "    ],",
            ")",
            "",
            "agent = build_supervisor_agent(config)",
            "",
        ])

    # Add run block
    lines.extend([
        "",
        'if __name__ == "__main__":',
        "    import asyncio",
        "    from langchain_core.messages import HumanMessage",
        "",
        '    async def main():',
        '        result = await agent.ainvoke(',
        '            {"messages": [HumanMessage(content="Hello! What can you do?")]},',
        '            config={"configurable": {"thread_id": "test"}},',
        '        )',
        '        print(result["messages"][-1].content)',
        "",
        '    asyncio.run(main())',
    ])

    return "\n".join(lines)
