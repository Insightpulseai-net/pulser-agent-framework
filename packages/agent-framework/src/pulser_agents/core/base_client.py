"""
Base chat client abstraction.

Defines the interface that all LLM provider clients must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field

from pulser_agents.core.message import Message
from pulser_agents.core.response import AgentResponse, StreamingChunk


class ChatClientConfig(BaseModel):
    """
    Configuration for chat clients.

    Common configuration options shared across providers.
    """

    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: list[str] | None = None
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

    # Provider-specific
    api_key: str | None = None
    base_url: str | None = None
    organization: str | None = None

    # Azure-specific
    azure_endpoint: str | None = None
    azure_deployment: str | None = None
    api_version: str | None = None

    # Feature flags
    streaming: bool = False
    json_mode: bool = False


class ToolDefinition(BaseModel):
    """Definition of a tool/function for the LLM."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required,
                },
            },
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required,
            },
        }


class BaseChatClient(ABC):
    """
    Abstract base class for all chat clients.

    Defines the interface that provider-specific clients must implement.

    Example:
        >>> class MyChatClient(BaseChatClient):
        ...     async def chat(self, messages, **kwargs):
        ...         # Implementation
        ...         pass
    """

    def __init__(self, config: ChatClientConfig | None = None) -> None:
        self.config = config or ChatClientConfig()

    @property
    def model(self) -> str:
        """Get the model name."""
        return self.config.model

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any
    ) -> AgentResponse:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tools available to the model
            **kwargs: Additional provider-specific options

        Returns:
            AgentResponse with the model's response
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any
    ) -> AsyncIterator[StreamingChunk]:
        """
        Send messages and stream the response.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tools available to the model
            **kwargs: Additional provider-specific options

        Yields:
            StreamingChunk objects as the response is generated
        """
        pass
        # This is an abstract method - yield is just for type checking
        if False:  # pragma: no cover
            yield StreamingChunk(id="", delta="")

    async def close(self) -> None:
        """Close the client and release resources."""
        pass

    async def __aenter__(self) -> BaseChatClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


class MockChatClient(BaseChatClient):
    """
    Mock chat client for testing.

    Returns predefined responses without calling any LLM.
    """

    def __init__(
        self,
        responses: list[str] | None = None,
        config: ChatClientConfig | None = None
    ) -> None:
        super().__init__(config)
        self._responses = responses or ["This is a mock response."]
        self._call_count = 0

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any
    ) -> AgentResponse:
        """Return a mock response."""
        response_text = self._responses[self._call_count % len(self._responses)]
        self._call_count += 1

        return AgentResponse(
            message=Message.assistant(content=response_text),
            model="mock-model",
            finish_reason="stop",
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any
    ) -> AsyncIterator[StreamingChunk]:
        """Stream a mock response."""
        response_text = self._responses[self._call_count % len(self._responses)]
        self._call_count += 1

        # Simulate streaming by yielding one word at a time
        words = response_text.split()
        for i, word in enumerate(words):
            is_last = i == len(words) - 1
            yield StreamingChunk(
                id=f"chunk-{i}",
                delta=word + ("" if is_last else " "),
                finish_reason="stop" if is_last else None,
            )
