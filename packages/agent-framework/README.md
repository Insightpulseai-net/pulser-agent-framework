# Pulser Agent Framework

A comprehensive multi-language framework for building, orchestrating, and deploying AI agents.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Azure OpenAI, Ollama
- **Orchestration Patterns**: Sequential, Concurrent, Group Chat, Handoff
- **Memory Systems**: In-memory, File-based, Redis, Vector Store
- **Tool Integration**: Function calling with type-safe definitions
- **Structured Logging**: Built on structlog for observability

## Installation

```bash
pip install pulser-agent-framework
```

With optional providers:

```bash
# All providers
pip install pulser-agent-framework[all]

# Specific providers
pip install pulser-agent-framework[openai]
pip install pulser-agent-framework[anthropic]
pip install pulser-agent-framework[azure]
pip install pulser-agent-framework[ollama]
```

## Quick Start

```python
from pulser_agents import Agent, OpenAIProvider
from pulser_agents.orchestration import SequentialOrchestrator

# Create an agent
agent = Agent(
    name="assistant",
    provider=OpenAIProvider(model="gpt-4"),
    system_prompt="You are a helpful assistant."
)

# Run a simple task
response = await agent.run("Hello, world!")
print(response.content)
```

## Orchestration Patterns

### Sequential Orchestration

```python
from pulser_agents.orchestration import SequentialOrchestrator

orchestrator = SequentialOrchestrator(agents=[agent1, agent2, agent3])
result = await orchestrator.run("Process this task")
```

### Concurrent Orchestration

```python
from pulser_agents.orchestration import ConcurrentOrchestrator

orchestrator = ConcurrentOrchestrator(agents=[agent1, agent2])
results = await orchestrator.run("Parallel task")
```

### Group Chat

```python
from pulser_agents.orchestration import GroupChatOrchestrator

orchestrator = GroupChatOrchestrator(
    agents=[researcher, writer, reviewer],
    max_rounds=5
)
result = await orchestrator.run("Write a research paper")
```

## Memory Systems

```python
from pulser_agents.memory import RedisMemory

memory = RedisMemory(redis_url="redis://localhost:6379")
agent = Agent(
    name="stateful_agent",
    provider=provider,
    memory=memory
)
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests

# Type checking
mypy src
```

## License

MIT License - see LICENSE file for details.
