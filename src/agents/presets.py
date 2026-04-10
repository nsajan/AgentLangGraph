"""Pre-built agent configurations for each pattern."""

from src.agent_builder.schemas import AgentConfig, AgentNodeConfig, PatternType, ToolConfig

REACT_CHATBOT = AgentConfig(
    name="react-chatbot",
    description="A conversational agent with calculator and time tools.",
    pattern=PatternType.REACT,
    agent=AgentNodeConfig(
        name="agent",
        system_prompt="You are a helpful assistant. Use tools when appropriate.",
        model="claude-sonnet-4-20250514",
        tools=[
            ToolConfig(name="calculator", description="Evaluate math expressions"),
            ToolConfig(name="current_time", description="Get current date/time"),
        ],
    ),
)

PLAN_EXECUTE_RESEARCHER = AgentConfig(
    name="plan-execute-researcher",
    description="Plans a research approach, then executes each step systematically.",
    pattern=PatternType.PLAN_EXECUTE,
    planner=AgentNodeConfig(
        name="planner",
        system_prompt="You are a research planner. Break complex questions into clear, sequential research steps.",
        model="claude-sonnet-4-20250514",
    ),
    executor=AgentNodeConfig(
        name="executor",
        system_prompt="You are a research executor. Complete the assigned step thoroughly and concisely.",
        model="claude-sonnet-4-20250514",
        tools=[
            ToolConfig(name="calculator", description="Evaluate math expressions"),
        ],
    ),
)

REFLECTION_WRITER = AgentConfig(
    name="reflection-writer",
    description="Writes content, then self-critiques and revises up to 3 times.",
    pattern=PatternType.REFLECTION,
    max_iterations=3,
    generator=AgentNodeConfig(
        name="writer",
        system_prompt="You are an expert writer. Produce clear, well-structured content based on the user's request.",
        model="claude-sonnet-4-20250514",
    ),
    critic=AgentNodeConfig(
        name="critic",
        system_prompt="You are a demanding editor. Review the draft for clarity, accuracy, structure, and completeness. Be specific in your feedback.",
        model="claude-sonnet-4-20250514",
    ),
)

SUPERVISOR_TEAM = AgentConfig(
    name="supervisor-team",
    description="A supervisor delegates to a researcher and a writer to produce well-researched content.",
    pattern=PatternType.SUPERVISOR,
    supervisor=AgentNodeConfig(
        name="supervisor",
        system_prompt="You manage a team. Route tasks to the right worker based on what's needed.",
        model="claude-sonnet-4-20250514",
    ),
    workers=[
        AgentNodeConfig(
            name="researcher",
            system_prompt="You are a thorough researcher. Provide detailed, factual analysis on the given topic.",
            model="claude-sonnet-4-20250514",
        ),
        AgentNodeConfig(
            name="writer",
            system_prompt="You are a skilled writer. Take research findings and produce polished, engaging content.",
            model="claude-sonnet-4-20250514",
        ),
    ],
)

PRESETS: dict[str, AgentConfig] = {
    "react-chatbot": REACT_CHATBOT,
    "plan-execute-researcher": PLAN_EXECUTE_RESEARCHER,
    "reflection-writer": REFLECTION_WRITER,
    "supervisor-team": SUPERVISOR_TEAM,
}
