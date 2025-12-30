"""
OpenAI chat client implementation.

Provides integration with OpenAI's GPT models.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from pulser_agents.core.base_client import (
    BaseChatClient,
    ChatClientConfig,
    ToolDefinition,
)
from pulser_agents.core.exceptions import (
    AuthenticationError,
    ContextLengthError,
    ModelNotFoundError,
    ProviderError,
    RateLimitError,
)
from pulser_agents.core.message import Message, ToolCall
from pulser_agents.core.response import AgentResponse, StreamingChunk, Usage


class OpenAIChatClient(BaseChatClient):
    """
    Chat client for OpenAI's API.

    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.

    Example:
        >>> client = OpenAIChatClient(
        ...     config=ChatClientConfig(
        ...         model="gpt-4o",
        ...         api_key="sk-...",
        ...     )
        ... )
        >>> response = await client.chat([Message.user("Hello!")])
    """

    def __init__(self, config: ChatClientConfig | None = None) -> None:
        super().__init__(config)
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Get or create the OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "openai package is required. Install with: pip install openai"
                )

            kwargs: dict[str, Any] = {}
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            if self.config.organization:
                kwargs["organization"] = self.config.organization
            if self.config.timeout:
                kwargs["timeout"] = self.config.timeout

            self._client = AsyncOpenAI(**kwargs)

        return self._client

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert messages to OpenAI format."""
        result = []
        for msg in messages:
            converted = msg.to_dict()
            # OpenAI expects 'arguments' as a JSON string
            if "tool_calls" in converted:
                for tc in converted["tool_calls"]:
                    if isinstance(tc.get("function", {}).get("arguments"), dict):
                        tc["function"]["arguments"] = json.dumps(
                            tc["function"]["arguments"]
                        )
            result.append(converted)
        return result

    def _parse_tool_calls(self, tool_calls: Any) -> list[ToolCall]:
        """Parse OpenAI tool calls into our format."""
        result = []
        for tc in tool_calls:
            args = tc.function.arguments
            if isinstance(args, str):
                args = json.loads(args)

            result.append(ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=args,
            ))
        return result

    def _handle_error(self, e: Exception) -> None:
        """Convert OpenAI errors to our exception types."""
        try:
            from openai import (
                APIError,
                BadRequestError,
                NotFoundError,
            )
            from openai import (
                AuthenticationError as OpenAIAuthError,
            )
            from openai import (
                RateLimitError as OpenAIRateLimitError,
            )
        except ImportError:
            raise e

        if isinstance(e, OpenAIAuthError):
            raise AuthenticationError(
                str(e),
                provider="openai",
            )
        elif isinstance(e, OpenAIRateLimitError):
            raise RateLimitError(
                str(e),
                provider="openai",
            )
        elif isinstance(e, NotFoundError):
            raise ModelNotFoundError(
                str(e),
                provider="openai",
            )
        elif isinstance(e, BadRequestError):
            if "context_length" in str(e).lower():
                raise ContextLengthError(
                    str(e),
                    provider="openai",
                )
            raise ProviderError(
                str(e),
                provider="openai",
            )
        elif isinstance(e, APIError):
            raise ProviderError(
                str(e),
                provider="openai",
                status_code=getattr(e, "status_code", None),
            )
        raise e

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Send messages to OpenAI and get a response."""
        client = self._get_client()

        # Build request
        request: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": self._convert_messages(messages),
        }

        if self.config.temperature is not None:
            request["temperature"] = kwargs.get("temperature", self.config.temperature)
        if self.config.max_tokens:
            request["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)
        if self.config.top_p:
            request["top_p"] = self.config.top_p
        if self.config.frequency_penalty:
            request["frequency_penalty"] = self.config.frequency_penalty
        if self.config.presence_penalty:
            request["presence_penalty"] = self.config.presence_penalty
        if self.config.stop:
            request["stop"] = self.config.stop
        if self.config.json_mode:
            request["response_format"] = {"type": "json_object"}

        # Add tools if provided
        if tools:
            request["tools"] = [t.to_openai_format() for t in tools]
            request["tool_choice"] = kwargs.get("tool_choice", "auto")

        try:
            response = await client.chat.completions.create(**request)
        except Exception as e:
            self._handle_error(e)

        # Parse response
        choice = response.choices[0]
        message = choice.message

        tool_calls = None
        if message.tool_calls:
            tool_calls = self._parse_tool_calls(message.tool_calls)

        return AgentResponse(
            message=Message.assistant(
                content=message.content or "",
                tool_calls=tool_calls,
            ),
            tool_calls=tool_calls,
            usage=Usage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            ),
            model=response.model,
            finish_reason=choice.finish_reason,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamingChunk]:
        """Stream a response from OpenAI."""
        client = self._get_client()

        # Build request
        request: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": self._convert_messages(messages),
            "stream": True,
        }

        if self.config.temperature is not None:
            request["temperature"] = kwargs.get("temperature", self.config.temperature)
        if self.config.max_tokens:
            request["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)

        # Add tools if provided
        if tools:
            request["tools"] = [t.to_openai_format() for t in tools]
            request["tool_choice"] = kwargs.get("tool_choice", "auto")

        try:
            stream = await client.chat.completions.create(**request)

            async for chunk in stream:
                if chunk.choices:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    yield StreamingChunk(
                        id=chunk.id,
                        delta=delta.content or "",
                        finish_reason=choice.finish_reason,
                    )

        except Exception as e:
            self._handle_error(e)

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            await self._client.close()
            self._client = None
