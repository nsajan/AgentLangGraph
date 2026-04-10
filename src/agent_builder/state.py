"""Shared state definitions for LangGraph agents."""

from __future__ import annotations

from typing import Annotated

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Default agent state that flows through the graph."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    current_node: str = ""
    metadata: dict = Field(default_factory=dict)
