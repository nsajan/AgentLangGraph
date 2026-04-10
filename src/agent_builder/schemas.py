"""Pydantic schemas for defining agents declaratively."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ToolConfig(BaseModel):
    """Configuration for a tool available to an agent node."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    function_path: str | None = None  # e.g. "src.agents.tools.web_search"


class NodeConfig(BaseModel):
    """Configuration for a single node in the agent graph."""

    name: str
    type: str = "llm"  # "llm" | "tool" | "human" | "conditional" | "custom"
    system_prompt: str | None = None
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4o"
    tools: list[ToolConfig] = Field(default_factory=list)
    custom_function_path: str | None = None  # for type="custom"


class EdgeConfig(BaseModel):
    """Configuration for an edge between nodes."""

    source: str
    target: str
    condition: str | None = None  # Python expression or function path for conditional edges


class AgentConfig(BaseModel):
    """Full declarative configuration for a LangGraph agent."""

    name: str
    description: str = ""
    nodes: list[NodeConfig]
    edges: list[EdgeConfig]
    entry_point: str
    finish_point: str | None = None

    model_config = {"json_schema_extra": {
        "examples": [{
            "name": "simple-chatbot",
            "description": "A simple chatbot with tool use",
            "nodes": [
                {"name": "agent", "type": "llm", "system_prompt": "You are a helpful assistant.", "tools": []},
            ],
            "edges": [],
            "entry_point": "agent",
        }]
    }}
