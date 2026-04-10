"""API routes for the playground."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agent_builder.builder import AgentBuilder
from src.agent_builder.schemas import AgentConfig
from src.agents.presets import PRESETS

router = APIRouter()

# In-memory session store: session_id -> compiled graph
_sessions: dict[str, Any] = {}
_session_configs: dict[str, AgentConfig] = {}
_session_histories: dict[str, list[dict]] = {}


# --- Request / Response models ---

class CreateSessionRequest(BaseModel):
    config: AgentConfig | None = None
    preset: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    agent_name: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    messages: list[dict]
    current_node: str


# --- Routes ---

@router.get("/presets")
async def list_presets():
    """List available preset agent configurations."""
    return {name: cfg.model_dump() for name, cfg in PRESETS.items()}


@router.get("/presets/{name}")
async def get_preset(name: str):
    """Get a single preset config."""
    if name not in PRESETS:
        raise HTTPException(404, f"Preset '{name}' not found")
    return PRESETS[name].model_dump()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    """Create a new agent session from a config or preset."""
    if req.preset:
        if req.preset not in PRESETS:
            raise HTTPException(404, f"Preset '{req.preset}' not found")
        config = PRESETS[req.preset]
    elif req.config:
        config = req.config
    else:
        raise HTTPException(400, "Provide either 'config' or 'preset'")

    session_id = str(uuid.uuid4())[:8]
    builder = AgentBuilder(config)
    graph = builder.build()

    _sessions[session_id] = graph
    _session_configs[session_id] = config
    _session_histories[session_id] = []

    return CreateSessionResponse(session_id=session_id, agent_name=config.name)


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(session_id: str, req: ChatRequest):
    """Send a message to a running agent session."""
    if session_id not in _sessions:
        raise HTTPException(404, f"Session '{session_id}' not found")

    graph = _sessions[session_id]
    history = _session_histories[session_id]

    history.append({"role": "user", "content": req.message})

    result = await graph.ainvoke({"messages": [HumanMessage(content=req.message)]})

    last_ai = result["messages"][-1]
    response_text = last_ai.content if hasattr(last_ai, "content") else str(last_ai)

    history.append({"role": "assistant", "content": response_text})

    return ChatResponse(
        response=response_text,
        messages=history,
        current_node=result.get("current_node", ""),
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session info."""
    if session_id not in _sessions:
        raise HTTPException(404, f"Session '{session_id}' not found")
    config = _session_configs[session_id]
    return {
        "session_id": session_id,
        "agent_name": config.name,
        "config": config.model_dump(),
        "history": _session_histories.get(session_id, []),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    for store in (_sessions, _session_configs, _session_histories):
        store.pop(session_id, None)
    return {"deleted": session_id}


@router.post("/validate")
async def validate_config(config: AgentConfig):
    """Validate an agent config without creating a session."""
    try:
        builder = AgentBuilder(config)
        builder.build()
        return {"valid": True, "errors": []}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}
