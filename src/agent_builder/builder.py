"""Main AgentBuilder — dispatches to pattern-specific builders."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from src.agent_builder.patterns import (
    build_plan_execute_agent,
    build_react_agent,
    build_reflection_agent,
    build_supervisor_agent,
)
from src.agent_builder.schemas import AgentConfig, PatternType

_BUILDERS = {
    PatternType.REACT: build_react_agent,
    PatternType.PLAN_EXECUTE: build_plan_execute_agent,
    PatternType.REFLECTION: build_reflection_agent,
    PatternType.SUPERVISOR: build_supervisor_agent,
}


class AgentBuilder:
    """Build a LangGraph agent from a pattern-based config."""

    def __init__(self, config: AgentConfig):
        self.config = config

    def build(self, *, use_checkpointer: bool = True):
        """Compile the config into a runnable LangGraph."""
        builder_fn = _BUILDERS.get(self.config.pattern)
        if not builder_fn:
            raise ValueError(f"Unknown pattern: {self.config.pattern}")

        checkpointer = MemorySaver() if use_checkpointer else None
        return builder_fn(self.config, checkpointer=checkpointer)

    def validate(self) -> list[str]:
        """Validate the config without building. Returns list of errors."""
        errors = []
        p = self.config.pattern

        if p == PatternType.REACT and not self.config.agent:
            errors.append("ReAct pattern requires 'agent' configuration")
        elif p == PatternType.PLAN_EXECUTE:
            if not self.config.planner:
                errors.append("Plan & Execute requires 'planner' configuration")
            if not self.config.executor:
                errors.append("Plan & Execute requires 'executor' configuration")
        elif p == PatternType.REFLECTION:
            if not self.config.generator:
                errors.append("Reflection requires 'generator' configuration")
            if not self.config.critic:
                errors.append("Reflection requires 'critic' configuration")
        elif p == PatternType.SUPERVISOR:
            if not self.config.supervisor:
                errors.append("Supervisor requires 'supervisor' configuration")
            if not self.config.workers:
                errors.append("Supervisor requires at least one worker")

        return errors
