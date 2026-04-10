"""Declarative schemas for pattern-based agent configuration."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PatternType(str, Enum):
    REACT = "react"
    PLAN_EXECUTE = "plan_execute"
    REFLECTION = "reflection"
    SUPERVISOR = "supervisor"


class ToolConfig(BaseModel):
    """A tool available to an agent."""

    name: str
    description: str = ""


class AgentNodeConfig(BaseModel):
    """Configuration for an LLM-backed agent within a pattern."""

    name: str
    system_prompt: str = "You are a helpful assistant."
    model: str = "claude-sonnet-4-20250514"
    tools: list[ToolConfig] = Field(default_factory=list)


class StateFieldConfig(BaseModel):
    """A custom field in the agent's state (beyond messages)."""

    name: str
    field_type: str = "str"  # str, list, dict, int, bool
    default: Any = None
    description: str = ""


class AgentConfig(BaseModel):
    """Full configuration for a pattern-based agent."""

    name: str
    description: str = ""
    pattern: PatternType

    # --- Pattern-specific config ---

    # ReAct: single agent + tools
    agent: AgentNodeConfig | None = None

    # Plan & Execute: planner + executor
    planner: AgentNodeConfig | None = None
    executor: AgentNodeConfig | None = None

    # Reflection: generator + critic, with max iterations
    generator: AgentNodeConfig | None = None
    critic: AgentNodeConfig | None = None
    max_iterations: int = 3

    # Supervisor: router + workers
    supervisor: AgentNodeConfig | None = None
    workers: list[AgentNodeConfig] = Field(default_factory=list)

    # Custom state fields (all patterns)
    state_fields: list[StateFieldConfig] = Field(default_factory=list)
