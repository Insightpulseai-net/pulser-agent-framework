"""
Core module for the Pulser Agent Framework.

Contains base classes and abstractions for agents, messages, and responses.
"""

from pulser_agents.core.agent import Agent, AgentConfig
from pulser_agents.core.base_client import BaseChatClient, ChatClientConfig
from pulser_agents.core.context import AgentContext, ConversationHistory
from pulser_agents.core.exceptions import (
    AgentError,
    OrchestrationError,
    ProviderError,
    ToolError,
)
from pulser_agents.core.message import Message, MessageRole
from pulser_agents.core.response import AgentResponse, StreamingResponse

__all__ = [
    "Agent",
    "AgentConfig",
    "Message",
    "MessageRole",
    "AgentResponse",
    "StreamingResponse",
    "AgentContext",
    "ConversationHistory",
    "BaseChatClient",
    "ChatClientConfig",
    "AgentError",
    "ProviderError",
    "ToolError",
    "OrchestrationError",
]
