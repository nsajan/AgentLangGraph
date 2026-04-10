"""Tests for agent builder schemas and config validation."""

from src.agent_builder.schemas import AgentConfig, AgentNodeConfig, PatternType, ToolConfig


def test_react_config():
    config = AgentConfig(
        name="test",
        pattern=PatternType.REACT,
        agent=AgentNodeConfig(name="agent"),
    )
    assert config.pattern == PatternType.REACT
    assert config.agent.name == "agent"


def test_plan_execute_config():
    config = AgentConfig(
        name="test",
        pattern=PatternType.PLAN_EXECUTE,
        planner=AgentNodeConfig(name="planner"),
        executor=AgentNodeConfig(name="executor", tools=[ToolConfig(name="calculator")]),
    )
    assert len(config.executor.tools) == 1


def test_reflection_config():
    config = AgentConfig(
        name="test",
        pattern=PatternType.REFLECTION,
        max_iterations=5,
        generator=AgentNodeConfig(name="gen"),
        critic=AgentNodeConfig(name="critic"),
    )
    assert config.max_iterations == 5


def test_supervisor_config():
    config = AgentConfig(
        name="test",
        pattern=PatternType.SUPERVISOR,
        supervisor=AgentNodeConfig(name="sup"),
        workers=[
            AgentNodeConfig(name="w1"),
            AgentNodeConfig(name="w2"),
        ],
    )
    assert len(config.workers) == 2


def test_config_serialization():
    config = AgentConfig(
        name="test",
        pattern=PatternType.REACT,
        agent=AgentNodeConfig(name="agent", tools=[ToolConfig(name="echo")]),
    )
    data = config.model_dump()
    restored = AgentConfig(**data)
    assert restored.agent.tools[0].name == "echo"


def test_builder_validation():
    from src.agent_builder.builder import AgentBuilder

    # Missing agent for react
    config = AgentConfig(name="bad", pattern=PatternType.REACT)
    errors = AgentBuilder(config).validate()
    assert len(errors) > 0

    # Valid react
    config = AgentConfig(name="good", pattern=PatternType.REACT, agent=AgentNodeConfig(name="a"))
    errors = AgentBuilder(config).validate()
    assert len(errors) == 0


def test_presets_valid():
    from src.agent_builder.builder import AgentBuilder
    from src.agents.presets import PRESETS

    for name, cfg in PRESETS.items():
        errors = AgentBuilder(cfg).validate()
        assert errors == [], f"Preset '{name}' has validation errors: {errors}"
