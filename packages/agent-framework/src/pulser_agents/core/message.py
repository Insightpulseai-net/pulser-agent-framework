"""
Message types and utilities for the agent framework.

Messages represent the fundamental unit of communication between agents,
users, and LLM providers.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in the conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"  # Legacy, prefer TOOL


class ContentType(str, Enum):
    """Type of content in a message."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    FILE = "file"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class TextContent(BaseModel):
    """Text content in a message."""

    type: ContentType = ContentType.TEXT
    text: str


class ImageContent(BaseModel):
    """Image content in a message."""

    type: ContentType = ContentType.IMAGE
    source_type: str = "base64"  # or "url"
    media_type: str = "image/png"
    data: str  # base64 or URL


class FileContent(BaseModel):
    """File content in a message."""

    type: ContentType = ContentType.FILE
    file_id: str
    filename: str
    mime_type: str


class ToolCall(BaseModel):
    """A tool/function call made by the assistant."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result from a tool/function execution."""

    tool_call_id: str
    name: str
    content: str
    is_error: bool = False


# Union type for all content types
MessageContent = Union[str, TextContent, ImageContent, FileContent, ToolCall, ToolResult, list]


class Message(BaseModel):
    """
    A message in a conversation.

    Messages can contain various types of content including text, images,
    files, and tool calls/results.

    Attributes:
        id: Unique identifier for the message
        role: The role of the message sender
        content: The content of the message
        name: Optional name for the message sender
        tool_calls: Optional list of tool calls made by the assistant
        tool_call_id: Optional ID linking to a tool call (for tool results)
        metadata: Optional metadata for the message
        created_at: Timestamp when the message was created

    Example:
        >>> msg = Message(
        ...     role=MessageRole.USER,
        ...     content="Hello, how are you?"
        ... )
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: MessageContent
    name: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

    @classmethod
    def system(cls, content: str, **kwargs: Any) -> Message:
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content, **kwargs)

    @classmethod
    def user(cls, content: MessageContent, **kwargs: Any) -> Message:
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content, **kwargs)

    @classmethod
    def assistant(
        cls,
        content: str | None = None,
        tool_calls: list[ToolCall] | None = None,
        **kwargs: Any
    ) -> Message:
        """Create an assistant message."""
        return cls(
            role=MessageRole.ASSISTANT,
            content=content or "",
            tool_calls=tool_calls,
            **kwargs
        )

    @classmethod
    def tool_result(
        cls,
        tool_call_id: str,
        name: str,
        content: str,
        is_error: bool = False,
        **kwargs: Any
    ) -> Message:
        """Create a tool result message."""
        return cls(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            metadata={"is_error": is_error, **kwargs.pop("metadata", {})},
            **kwargs
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for API calls."""
        result: dict[str, Any] = {
            "role": self.role,
            "content": self._serialize_content(),
        }

        if self.name:
            result["name"] = self.name

        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        return result

    def _serialize_content(self) -> Any:
        """Serialize content for API calls."""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            return [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in self.content
            ]
        elif isinstance(self.content, BaseModel):
            return self.content.model_dump()
        return self.content

    @property
    def text(self) -> str:
        """Get the text content of the message."""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, TextContent):
            return self.content.text
        elif isinstance(self.content, list):
            texts = []
            for item in self.content:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, TextContent):
                    texts.append(item.text)
            return "\n".join(texts)
        return ""


class MessageBuilder:
    """
    Builder for constructing complex messages.

    Example:
        >>> msg = (MessageBuilder()
        ...     .role(MessageRole.USER)
        ...     .text("Check this image:")
        ...     .image(base64_data, "image/png")
        ...     .build())
    """

    def __init__(self) -> None:
        self._role: MessageRole = MessageRole.USER
        self._content: list[Any] = []
        self._name: str | None = None
        self._metadata: dict[str, Any] = {}

    def role(self, role: MessageRole) -> MessageBuilder:
        """Set the message role."""
        self._role = role
        return self

    def name(self, name: str) -> MessageBuilder:
        """Set the sender name."""
        self._name = name
        return self

    def text(self, text: str) -> MessageBuilder:
        """Add text content."""
        self._content.append(TextContent(text=text))
        return self

    def image(
        self,
        data: str,
        media_type: str = "image/png",
        source_type: str = "base64"
    ) -> MessageBuilder:
        """Add image content."""
        self._content.append(ImageContent(
            data=data,
            media_type=media_type,
            source_type=source_type
        ))
        return self

    def file(self, file_id: str, filename: str, mime_type: str) -> MessageBuilder:
        """Add file content."""
        self._content.append(FileContent(
            file_id=file_id,
            filename=filename,
            mime_type=mime_type
        ))
        return self

    def metadata(self, key: str, value: Any) -> MessageBuilder:
        """Add metadata."""
        self._metadata[key] = value
        return self

    def build(self) -> Message:
        """Build the message."""
        content: MessageContent
        if len(self._content) == 0:
            content = ""
        elif len(self._content) == 1 and isinstance(self._content[0], TextContent):
            content = self._content[0].text
        else:
            content = self._content

        return Message(
            role=self._role,
            content=content,
            name=self._name,
            metadata=self._metadata
        )
