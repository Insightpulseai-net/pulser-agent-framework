"""
Ollama chat client implementation.

Provides integration with locally-hosted models via Ollama.
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
    ModelNotFoundError,
    ProviderError,
)
from pulser_agents.core.message import Message, MessageRole, ToolCall
from pulser_agents.core.response import AgentResponse, StreamingChunk, Usage


class OllamaChatClient(BaseChatClient):
    """
    Chat client for Ollama local models.

    Supports any model available in your local Ollama installation.

    Example:
        >>> client = OllamaChatClient(
        ...     config=ChatClientConfig(
        ...         model="llama3.2",
        ...         base_url="http://localhost:11434",
        ...     )
        ... )
        >>> response = await client.chat([Message.user("Hello!")])
    """

    def __init__(self, config: ChatClientConfig | None = None) -> None:
        super().__init__(config)
        # Override default model for Ollama
        if self.config.model == "gpt-4o":
            self.config.model = "llama3.2"
        if not self.config.base_url:
            self.config.base_url = "http://localhost:11434"
        self._client: Any | None = None

    def _get_client(self) -> Any:
        """Get or create the Ollama client."""
        if self._client is None:
            try:
                from ollama import AsyncClient
            except ImportError:
                raise ImportError(
                    "ollama package is required. Install with: pip install ollama"
                )

            self._client = AsyncClient(host=self.config.base_url)

        return self._client

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert messages to Ollama format."""
        result = []
        for msg in messages:
            role = msg.role
            if role == MessageRole.SYSTEM:
                role = "system"
            elif role == MessageRole.USER:
                role = "user"
            elif role == MessageRole.ASSISTANT:
                role = "assistant"
            elif role == MessageRole.TOOL:
                # Ollama doesn't have native tool support, inject as user message
                role = "user"

            content = msg.text

            # Handle tool results
            if msg.role == MessageRole.TOOL:
                content = f"Tool result for {msg.name}:\n{msg.text}"

            result.append({
                "role": role,
                "content": content,
            })

        return result

    def _handle_error(self, e: Exception) -> None:
        """Convert Ollama errors to our exception types."""
        error_str = str(e).lower()

        if "not found" in error_str or "pull" in error_str:
            raise ModelNotFoundError(
                str(e),
                provider="ollama",
            )
        raise ProviderError(
            str(e),
            provider="ollama",
        )

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Send messages to Ollama and get a response."""
        client = self._get_client()

        # Build request
        options: dict[str, Any] = {}
        if self.config.temperature is not None:
            options["temperature"] = kwargs.get("temperature", self.config.temperature)
        if self.config.top_p:
            options["top_p"] = self.config.top_p
        if self.config.max_tokens:
            options["num_predict"] = kwargs.get("max_tokens", self.config.max_tokens)

        # If tools are provided, inject tool descriptions into system message
        converted_messages = self._convert_messages(messages)
        if tools:
            tool_prompt = self._build_tool_prompt(tools)
            # Prepend or append to system message
            if converted_messages and converted_messages[0]["role"] == "system":
                converted_messages[0]["content"] += f"\n\n{tool_prompt}"
            else:
                converted_messages.insert(0, {
                    "role": "system",
                    "content": tool_prompt,
                })

        try:
            response = await client.chat(
                model=kwargs.get("model", self.config.model),
                messages=converted_messages,
                options=options if options else None,
            )
        except Exception as e:
            self._handle_error(e)

        # Parse response
        content = response.get("message", {}).get("content", "")

        # Try to parse tool calls from the response
        tool_calls = None
        if tools:
            tool_calls = self._parse_tool_calls_from_text(content, tools)

        return AgentResponse(
            message=Message.assistant(
                content=content,
                tool_calls=tool_calls,
            ),
            tool_calls=tool_calls,
            usage=Usage(
                prompt_tokens=response.get("prompt_eval_count", 0),
                completion_tokens=response.get("eval_count", 0),
                total_tokens=(
                    response.get("prompt_eval_count", 0) +
                    response.get("eval_count", 0)
                ),
            ),
            model=response.get("model", self.config.model),
            finish_reason="stop",
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamingChunk]:
        """Stream a response from Ollama."""
        client = self._get_client()

        # Build request
        options: dict[str, Any] = {}
        if self.config.temperature is not None:
            options["temperature"] = kwargs.get("temperature", self.config.temperature)
        if self.config.max_tokens:
            options["num_predict"] = kwargs.get("max_tokens", self.config.max_tokens)

        converted_messages = self._convert_messages(messages)
        if tools:
            tool_prompt = self._build_tool_prompt(tools)
            if converted_messages and converted_messages[0]["role"] == "system":
                converted_messages[0]["content"] += f"\n\n{tool_prompt}"
            else:
                converted_messages.insert(0, {
                    "role": "system",
                    "content": tool_prompt,
                })

        try:
            stream = await client.chat(
                model=kwargs.get("model", self.config.model),
                messages=converted_messages,
                options=options if options else None,
                stream=True,
            )

            chunk_id = 0
            async for part in stream:
                content = part.get("message", {}).get("content", "")
                done = part.get("done", False)

                yield StreamingChunk(
                    id=f"chunk-{chunk_id}",
                    delta=content,
                    finish_reason="stop" if done else None,
                )
                chunk_id += 1

        except Exception as e:
            self._handle_error(e)

    def _build_tool_prompt(self, tools: list[ToolDefinition]) -> str:
        """Build a prompt describing available tools for the model."""
        tool_descriptions = []
        for tool in tools:
            params = json.dumps(tool.parameters, indent=2)
            tool_descriptions.append(
                f"### {tool.name}\n"
                f"Description: {tool.description}\n"
                f"Parameters:\n```json\n{params}\n```\n"
                f"Required: {', '.join(tool.required) if tool.required else 'none'}"
            )

        return (
            "## Available Tools\n"
            "You have access to the following tools. To use a tool, respond with "
            "a JSON object in this format:\n"
            '```json\n{"tool": "tool_name", "arguments": {"arg1": "value1"}}\n```\n\n'
            + "\n\n".join(tool_descriptions)
        )

    def _parse_tool_calls_from_text(
        self,
        text: str,
        tools: list[ToolDefinition],
    ) -> list[ToolCall] | None:
        """
        Try to parse tool calls from model output text.

        Since Ollama doesn't have native tool support, we look for
        JSON blocks in the response.
        """
        import re
        from uuid import uuid4

        # Look for JSON blocks
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, text)

        if not matches:
            # Try to find inline JSON
            json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
            matches = re.findall(json_pattern, text)

        tool_calls = []
        tool_names = {t.name for t in tools}

        for match in matches:
            try:
                data = json.loads(match)
                if "tool" in data and data["tool"] in tool_names:
                    tool_calls.append(ToolCall(
                        id=str(uuid4()),
                        name=data["tool"],
                        arguments=data.get("arguments", {}),
                    ))
            except json.JSONDecodeError:
                continue

        return tool_calls if tool_calls else None

    async def close(self) -> None:
        """Close the client."""
        self._client = None

    async def list_models(self) -> list[str]:
        """List available models in Ollama."""
        client = self._get_client()
        try:
            response = await client.list()
            return [m["name"] for m in response.get("models", [])]
        except Exception as e:
            self._handle_error(e)
            return []

    async def pull_model(self, model: str) -> None:
        """Pull a model from Ollama library."""
        client = self._get_client()
        try:
            await client.pull(model)
        except Exception as e:
            self._handle_error(e)
