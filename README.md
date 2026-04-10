# AgentLangGraph

An **Agent Builder & Testing Playground** built with [LangGraph](https://github.com/langchain-ai/langgraph).

Define agents declaratively as JSON configs (nodes, edges, tools), then test them interactively through a web playground.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Set your API keys
cp .env.example .env
# Edit .env with your keys

# Start the playground
python run.py
```

Open [http://localhost:8000](http://localhost:8000) to use the playground.

## Architecture

```
src/
  agent_builder/     # Core framework
    builder.py       # Compiles AgentConfig -> LangGraph
    schemas.py       # Pydantic models for declarative agent configs
    state.py         # Shared graph state
    tools.py         # Built-in tools + tool resolution
  agents/
    presets.py       # Pre-built agent configs (chatbot, calculator, multi-step)
  playground/
    api/             # FastAPI backend
      main.py        # App entry point
      routes.py      # REST API (sessions, chat, presets)
    frontend/        # Web UI
      templates/     # HTML
      static/        # CSS + JS
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/presets` | List preset agent configs |
| POST | `/api/sessions` | Create agent session (from preset or custom config) |
| POST | `/api/sessions/{id}/chat` | Send message to agent |
| POST | `/api/validate` | Validate an agent config |

## Creating Custom Agents

```json
{
  "name": "my-agent",
  "description": "A custom agent",
  "nodes": [
    {
      "name": "agent",
      "type": "llm",
      "system_prompt": "You are a helpful assistant.",
      "provider": "openai",
      "model": "gpt-4o",
      "tools": [
        {"name": "calculator", "description": "Math tool"}
      ]
    }
  ],
  "edges": [],
  "entry_point": "agent"
}
```

## Tests

```bash
pytest tests/
```
