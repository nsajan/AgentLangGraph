# AgentLangGraph

A **Pattern-Based Agent Builder & Testing Playground** powered by [LangGraph](https://github.com/langchain-ai/langgraph) and Anthropic Claude.

Build agents by selecting an architecture pattern, configuring the nodes, and testing interactively — no code required. Export to JSON or Python when ready.

## Agent Patterns

| Pattern | What it does |
|---------|-------------|
| **ReAct** | Single agent + tools in a loop (uses `create_react_agent`) |
| **Plan & Execute** | Planner creates steps → Executor runs each with tools → Synthesize |
| **Reflection** | Generator drafts → Critic reviews → Loop until approved |
| **Supervisor** | Router agent delegates to specialized worker agents |

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Set your API key
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY at minimum

# Start the playground
python run.py
```

Open [http://localhost:8000](http://localhost:8000).

## Architecture

```
src/
  agent_builder/
    builder.py         # Main builder — dispatches to pattern builders
    schemas.py         # Pydantic models (AgentConfig, PatternType, etc.)
    state.py           # Dynamic state factory for custom fields
    llm.py             # Centralized LLM factory (Anthropic)
    tools.py           # Built-in tools + resolution
    patterns/
      react.py         # ReAct via create_react_agent
      plan_execute.py  # Plan & Execute with custom state
      reflection.py    # Generator/Critic loop
      supervisor.py    # Supervisor + worker sub-agents
  agents/
    presets.py         # Pre-built configs for each pattern
  playground/
    api/               # FastAPI with SSE streaming + checkpointing
    frontend/          # Web UI (pattern config, flow viz, chat)
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/presets` | List preset agent configs |
| POST | `/api/sessions` | Create agent session |
| POST | `/api/sessions/{id}/chat` | Send message |
| POST | `/api/sessions/{id}/chat/stream` | Stream response (SSE) |
| POST | `/api/validate` | Validate config |
| POST | `/api/export/python` | Generate standalone Python script |

## Tests

```bash
pytest tests/ -v
```
