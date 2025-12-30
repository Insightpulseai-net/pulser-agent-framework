"""
Anthropic chat client implementation.

Provides integration with Anthropic's Claude models.
"""

from __future__ import annotations

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
from pulser_agents.core.message import Message, MessageRole, ToolCall
from pulser_agents.core.response import AgentResponse, StreamingChunk, Usage


class AnthropicChatClient(BaseChatClient):
    """
    Chat client for Anthropic's Claude API.

    Supports Claude 3 (Opus, Sonnet, Haiku) and other Claude models.

    Example:
        >>> client = AnthropicChatClient(
        ...     config=ChatClientConfig(
        ...         model="claude-3-5-sonnet-20241022",
        ...         api_key="sk-ant-...",
        ...     )
        ... )
        >>> response = await client.chat([Message.user("Hello!")])
    """

    def __init__(self, config: ChatClientConfig | None = None) -> None:
        super().__init__(config)
        # Override default model for Anthropic
        if self.config.model == "gpt-4o":
            self.config.model = "claude-3-5-sonnet-20241022"
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
            except ImportError:
                raise ImportError(
                    "anthropic package is required. Install with: pip install anthropic"
                )

            kwargs: dict[str, Any] = {}
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            if self.config.timeout:
                kwargs["timeout"] = self.config.timeout

            self._client = AsyncAnthropic(**kwargs)

        return self._client

    def _convert_messages(
        self, messages: list[Message]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Convert messages to Anthropic format.

        Returns (system_prompt, messages) since Anthropic handles system
        messages differently.
        """
        system_prompt = None
        converted = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Anthropic uses a separate system parameter
                system_prompt = msg.text
                continue

            content: Any = msg.text

            # Handle multimodal content
            if isinstance(msg.content, list):
                content = []
                for item in msg.content:
                    if hasattr(item, "type"):
                        if item.type == "text":
                            content.append({"type": "text", "text": item.text})
                        elif item.type == "image":
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": item.source_type,
                                    "media_type": item.media_type,
                                    "data": item.data,
                                }
                            })
                    elif isinstance(item, str):
                        content.append({"type": "text", "text": item})

            role = "user" if msg.role == MessageRole.USER else "assistant"

            # Handle tool results
            if msg.role == MessageRole.TOOL:
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.text,
                        "is_error": msg.metadata.get("is_error", False),
                    }]
                })
                continue

            # Handle assistant messages with tool calls
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                assistant_content = []
                if msg.text:
                    assistant_content.append({"type": "text", "text": msg.text})
                for tc in msg.tool_calls:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                converted.append({
                    "role": "assistant",
                    "content": assistant_content,
                })
                continue

            converted.append({
                "role": role,
                "content": content,
            })

        return system_prompt, converted

    def _parse_tool_calls(self, content: list[Any]) -> list[ToolCall]:
        """Parse Anthropic tool use blocks into our format."""
        result = []
        for block in content:
            if hasattr(block, "type") and block.type == "tool_use":
                result.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))
        return result

    def _extract_text(self, content: list[Any]) -> str:
        """Extract text from Anthropic content blocks."""
        texts = []
        for block in content:
            if hasattr(block, "type") and block.type == "text":
                texts.append(block.text)
        return "\n".join(texts)

    def _handle_error(self, e: Exception) -> None:
        """Convert Anthropic errors to our exception types."""
        try:
            from anthropic import (
                APIError,
                BadRequestError,
                NotFoundError,
            )
            from anthropic import (
                AuthenticationError as AnthropicAuthError,
            )
            from anthropic import (
                RateLimitError as AnthropicRateLimitError,
            )
        except ImportError:
            raise e

        if isinstance(e, AnthropicAuthError):
            raise AuthenticationError(
                str(e),
                provider="anthropic",
            )
        elif isinstance(e, AnthropicRateLimitError):
            raise RateLimitError(
                str(e),
                provider="anthropic",
            )
        elif isinstance(e, NotFoundError):
            raise ModelNotFoundError(
                str(e),
                provider="anthropic",
            )
        elif isinstance(e, BadRequestError):
            if "context" in str(e).lower() or "token" in str(e).lower():
                raise ContextLengthError(
                    str(e),
                    provider="anthropic",
                )
            raise ProviderError(
                str(e),
                provider="anthropic",
            )
        elif isinstance(e, APIError):
            raise ProviderError(
                str(e),
                provider="anthropic",
                status_code=getattr(e, "status_code", None),
            )
        raise e

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Send messages to Anthropic and get a response."""
        client = self._get_client()

        system_prompt, converted_messages = self._convert_messages(messages)

        # Build request
        request: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": converted_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
        }

        if system_prompt:
            request["system"] = system_prompt

        if self.config.temperature is not None:
            request["temperature"] = kwargs.get("temperature", self.config.temperature)
        if self.config.top_p:
            request["top_p"] = self.config.top_p
        if self.config.stop:
            request["stop_sequences"] = self.config.stop

        # Add tools if provided
        if tools:
            request["tools"] = [t.to_anthropic_format() for t in tools]

        try:
            response = await client.messages.create(**request)
        except Exception as e:
            self._handle_error(e)

        # Parse response
        text_content = self._extract_text(response.content)
        tool_calls = self._parse_tool_calls(response.content)

        return AgentResponse(
            message=Message.assistant(
                content=text_content,
                tool_calls=tool_calls if tool_calls else None,
            ),
            tool_calls=tool_calls if tool_calls else None,
            usage=Usage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            ),
            model=response.model,
            finish_reason=response.stop_reason,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamingChunk]:
        """Stream a response from Anthropic."""
        client = self._get_client()

        system_prompt, converted_messages = self._convert_messages(messages)

        # Build request
        request: dict[str, Any] = {
            "model": kwargs.get("model", self.config.model),
            "messages": converted_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 4096),
        }

        if system_prompt:
            request["system"] = system_prompt

        if self.config.temperature is not None:
            request["temperature"] = kwargs.get("temperature", self.config.temperature)

        # Add tools if provided
        if tools:
            request["tools"] = [t.to_anthropic_format() for t in tools]

        try:
            async with client.messages.stream(**request) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamingChunk(
                                id=f"chunk-{id(event)}",
                                delta=event.delta.text,
                            )
                    elif event.type == "message_stop":
                        yield StreamingChunk(
                            id="chunk-final",
                            delta="",
                            finish_reason="end_turn",
                        )

        except Exception as e:
            self._handle_error(e)

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            await self._client.close()
            self._client = None
