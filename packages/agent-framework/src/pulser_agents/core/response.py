"""
Response types for agent interactions.

Includes both complete responses and streaming responses.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from pulser_agents.core.message import Message, ToolCall


class Usage(BaseModel):
    """Token usage information from the provider."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def cost_estimate(self) -> float:
        """Estimate cost in USD (rough estimate, varies by model)."""
        # Rough estimate: $0.01 per 1K tokens
        return self.total_tokens * 0.00001


class AgentResponse(BaseModel):
    """
    Complete response from an agent.

    Attributes:
        id: Unique response identifier
        agent_name: Name of the responding agent
        message: The response message
        tool_calls: Optional list of tool calls made
        usage: Token usage statistics
        model: Model used for the response
        finish_reason: Why the response ended
        metadata: Additional response metadata
        created_at: When the response was created

    Example:
        >>> response = await agent.run("Hello!")
        >>> print(response.content)
        "Hello! How can I help you today?"
        >>> print(response.usage.total_tokens)
        42
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str | None = None
    message: Message
    tool_calls: list[ToolCall] | None = None
    usage: Usage = Field(default_factory=Usage)
    model: str | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def content(self) -> str:
        """Get the text content of the response."""
        return self.message.text

    @property
    def has_tool_calls(self) -> bool:
        """Check if the response includes tool calls."""
        return bool(self.tool_calls)

    def to_message(self) -> Message:
        """Convert response to a message for conversation history."""
        return self.message


class StreamingChunk(BaseModel):
    """A chunk of a streaming response."""

    id: str
    delta: str
    tool_call_delta: dict[str, Any] | None = None
    finish_reason: str | None = None
    usage: Usage | None = None


class StreamingResponse:
    """
    Streaming response from an agent.

    Allows iterating over response chunks as they arrive from the provider.

    Example:
        >>> async for chunk in agent.run_stream("Tell me a story"):
        ...     print(chunk.delta, end="", flush=True)
    """

    def __init__(
        self,
        stream: AsyncIterator[StreamingChunk],
        agent_name: str | None = None,
        model: str | None = None,
    ) -> None:
        self._stream = stream
        self._agent_name = agent_name
        self._model = model
        self._chunks: list[StreamingChunk] = []
        self._content: str = ""
        self._tool_calls: list[ToolCall] = []
        self._usage: Usage | None = None
        self._finish_reason: str | None = None
        self._completed = False

    async def __aiter__(self) -> AsyncIterator[StreamingChunk]:
        """Iterate over streaming chunks."""
        async for chunk in self._stream:
            self._chunks.append(chunk)
            self._content += chunk.delta

            if chunk.finish_reason:
                self._finish_reason = chunk.finish_reason

            if chunk.usage:
                self._usage = chunk.usage

            yield chunk

        self._completed = True

    async def collect(self) -> AgentResponse:
        """
        Collect all chunks and return a complete AgentResponse.

        This will consume the stream if not already consumed.
        """
        if not self._completed:
            async for _ in self:
                pass

        return AgentResponse(
            agent_name=self._agent_name,
            message=Message.assistant(content=self._content),
            tool_calls=self._tool_calls if self._tool_calls else None,
            usage=self._usage or Usage(),
            model=self._model,
            finish_reason=self._finish_reason,
        )

    @property
    def content(self) -> str:
        """Get the accumulated content so far."""
        return self._content

    @property
    def is_complete(self) -> bool:
        """Check if the stream is complete."""
        return self._completed


class RunResult(BaseModel):
    """
    Result of an agent run, potentially including multiple responses.

    Used when an agent makes multiple turns (e.g., tool calls).
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str | None = None
    responses: list[AgentResponse] = Field(default_factory=list)
    final_response: AgentResponse | None = None
    total_usage: Usage = Field(default_factory=Usage)
    iterations: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    @property
    def content(self) -> str:
        """Get the final response content."""
        if self.final_response:
            return self.final_response.content
        if self.responses:
            return self.responses[-1].content
        return ""

    @property
    def messages(self) -> list[Message]:
        """Get all messages from all responses."""
        return [r.message for r in self.responses]

    def add_response(self, response: AgentResponse) -> None:
        """Add a response and update totals."""
        self.responses.append(response)
        self.final_response = response
        self.iterations += 1
        self.total_usage.prompt_tokens += response.usage.prompt_tokens
        self.total_usage.completion_tokens += response.usage.completion_tokens
        self.total_usage.total_tokens += response.usage.total_tokens

    def complete(self) -> None:
        """Mark the run as complete."""
        self.completed_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> float | None:
        """Get the run duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
