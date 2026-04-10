"""Dynamic state factory for LangGraph agents."""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from pydantic import Field, create_model

from src.agent_builder.schemas import StateFieldConfig

# Map config type strings to Python types + defaults
_TYPE_MAP: dict[str, tuple[type, Any]] = {
    "str": (str, ""),
    "list": (list, []),
    "dict": (dict, {}),
    "int": (int, 0),
    "bool": (bool, False),
}


def create_state_class(
    extra_fields: list[StateFieldConfig] | None = None,
    name: str = "AgentState",
):
    """Build a Pydantic model with messages + custom fields.

    Returns a class compatible with LangGraph's StateGraph.
    """
    fields: dict[str, Any] = {
        "messages": (Annotated[list, add_messages], Field(default_factory=list)),
    }

    for sf in extra_fields or []:
        py_type, default = _TYPE_MAP.get(sf.field_type, (str, ""))
        if sf.default is not None:
            default = sf.default
        fields[sf.name] = (py_type, Field(default=default, description=sf.description))

    return create_model(name, **fields)
