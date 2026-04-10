"""Built-in tools that can be attached to agent nodes."""

from __future__ import annotations

import importlib
from typing import Any

from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Only supports basic arithmetic."""
    allowed = set("0123456789+-*/.()")
    if not all(c in allowed or c.isspace() for c in expression):
        return "Error: only basic arithmetic expressions are allowed."
    try:
        result = eval(expression)  # noqa: S307 – restricted to digits/operators
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def echo(text: str) -> str:
    """Echo back the given text. Useful for testing."""
    return text


BUILTIN_TOOLS = {
    "calculator": calculator,
    "echo": echo,
}


def resolve_tool(tool_config) -> Any:
    """Resolve a ToolConfig to an actual callable tool."""
    if tool_config.name in BUILTIN_TOOLS:
        return BUILTIN_TOOLS[tool_config.name]

    if tool_config.function_path:
        module_path, func_name = tool_config.function_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    raise ValueError(f"Unknown tool: {tool_config.name}")
