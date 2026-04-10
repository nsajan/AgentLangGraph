"""Pre-built agent configurations that ship with the playground."""

from src.agent_builder.schemas import AgentConfig, EdgeConfig, LLMProvider, NodeConfig, ToolConfig

SIMPLE_CHATBOT = AgentConfig(
    name="simple-chatbot",
    description="A minimal chatbot — single LLM node, no tools.",
    nodes=[
        NodeConfig(
            name="agent",
            type="llm",
            system_prompt="You are a friendly, helpful assistant.",
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
        ),
    ],
    edges=[],
    entry_point="agent",
    finish_point="agent",
)

CALCULATOR_AGENT = AgentConfig(
    name="calculator-agent",
    description="An assistant that can do math using a calculator tool.",
    nodes=[
        NodeConfig(
            name="agent",
            type="llm",
            system_prompt="You are a math tutor. Use the calculator tool when you need to compute something.",
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            tools=[ToolConfig(name="calculator", description="Evaluate math expressions")],
        ),
    ],
    edges=[],
    entry_point="agent",
)

MULTI_STEP_AGENT = AgentConfig(
    name="multi-step-agent",
    description="A two-node pipeline: a planner feeds into an executor.",
    nodes=[
        NodeConfig(
            name="planner",
            type="llm",
            system_prompt="You are a planning assistant. Break the user's request into clear steps. Output only the plan.",
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
        ),
        NodeConfig(
            name="executor",
            type="llm",
            system_prompt="You receive a plan from the planner. Execute each step and provide a final answer.",
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
        ),
    ],
    edges=[
        EdgeConfig(source="planner", target="executor"),
    ],
    entry_point="planner",
    finish_point="executor",
)

PRESETS: dict[str, AgentConfig] = {
    "simple-chatbot": SIMPLE_CHATBOT,
    "calculator-agent": CALCULATOR_AGENT,
    "multi-step-agent": MULTI_STEP_AGENT,
}
