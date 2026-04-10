"""Tool registry and resolution."""

from __future__ import annotations

import importlib
from typing import Any

from langchain_core.tools import tool

from src.agent_builder.schemas import ToolConfig


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Supports basic arithmetic."""
    allowed = set("0123456789+-*/.()")
    if not all(c in allowed or c.isspace() for c in expression):
        return "Error: only basic arithmetic expressions are allowed."
    try:
        result = eval(expression)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def echo(text: str) -> str:
    """Echo back the given text. Useful for testing tool calling."""
    return text


@tool
def current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


BUILTIN_TOOLS: dict[str, Any] = {
    "calculator": calculator,
    "echo": echo,
    "current_time": current_time,
}


def resolve_tools(tool_configs: list[ToolConfig]) -> list:
    """Resolve a list of ToolConfig to callable tools."""
    tools = []
    for tc in tool_configs:
        if tc.name in BUILTIN_TOOLS:
            tools.append(BUILTIN_TOOLS[tc.name])
        elif "." in tc.name:
            # Dynamic import: "my_module.my_tool"
            module_path, func_name = tc.name.rsplit(".", 1)
            module = importlib.import_module(module_path)
            tools.append(getattr(module, func_name))
        else:
            raise ValueError(f"Unknown tool: {tc.name}. Available: {list(BUILTIN_TOOLS.keys())}")
    return tools
