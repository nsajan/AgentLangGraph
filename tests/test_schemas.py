"""Tests for agent builder schemas and config validation."""

from src.agent_builder.schemas import AgentConfig, EdgeConfig, NodeConfig, ToolConfig


def test_minimal_config():
    config = AgentConfig(
        name="test",
        nodes=[NodeConfig(name="agent", type="llm")],
        edges=[],
        entry_point="agent",
    )
    assert config.name == "test"
    assert len(config.nodes) == 1


def test_config_with_tools():
    config = AgentConfig(
        name="tool-test",
        nodes=[
            NodeConfig(
                name="agent",
                type="llm",
                tools=[ToolConfig(name="calculator", description="math")],
            )
        ],
        edges=[],
        entry_point="agent",
    )
    assert len(config.nodes[0].tools) == 1
    assert config.nodes[0].tools[0].name == "calculator"


def test_multi_node_config():
    config = AgentConfig(
        name="multi",
        nodes=[
            NodeConfig(name="a", type="llm"),
            NodeConfig(name="b", type="llm"),
        ],
        edges=[EdgeConfig(source="a", target="b")],
        entry_point="a",
        finish_point="b",
    )
    assert len(config.edges) == 1
    assert config.edges[0].source == "a"


def test_config_serialization():
    config = AgentConfig(
        name="test",
        nodes=[NodeConfig(name="agent", type="llm")],
        edges=[],
        entry_point="agent",
    )
    data = config.model_dump()
    restored = AgentConfig(**data)
    assert restored.name == config.name


def test_presets_load():
    from src.agents.presets import PRESETS
    assert len(PRESETS) >= 3
    for name, cfg in PRESETS.items():
        assert cfg.name == name
        assert cfg.entry_point
