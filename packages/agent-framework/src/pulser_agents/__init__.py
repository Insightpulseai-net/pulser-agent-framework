"""
Pulser Agent Framework
======================

A comprehensive framework for building, orchestrating, and deploying AI agents.

Features:
- Multi-provider LLM support (OpenAI, Azure, Anthropic, Ollama)
- Flexible orchestration patterns (sequential, concurrent, group chat)
- Tool/function calling with type validation
- Memory and context management
- Middleware architecture for extensibility
- Streaming and async-first design

Example:
    >>> from pulser_agents import Agent, OpenAIChatClient
    >>>
    >>> client = OpenAIChatClient(api_key="sk-...")
    >>> agent = Agent(
    ...     chat_client=client,
    ...     instructions="You are a helpful assistant."
    ... )
    >>> response = await agent.run("Hello!")
"""

from pulser_agents.core.agent import Agent, AgentConfig
from pulser_agents.core.context import AgentContext, ConversationHistory
from pulser_agents.core.exceptions import (
    AgentError,
    OrchestrationError,
    ProviderError,
    ToolError,
)
from pulser_agents.core.message import Message, MessageRole
from pulser_agents.core.response import AgentResponse, StreamingResponse

# Version
__version__ = "0.1.0"

__all__ = [
    # Core
    "Agent",
    "AgentConfig",
    "Message",
    "MessageRole",
    "AgentResponse",
    "StreamingResponse",
    "AgentContext",
    "ConversationHistory",
    # Exceptions
    "AgentError",
    "ProviderError",
    "ToolError",
    "OrchestrationError",
    # Version
    "__version__",
]
