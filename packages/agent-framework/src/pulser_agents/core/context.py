"""
Context management for agent conversations.

Provides conversation history tracking, context windowing, and metadata storage.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from pulser_agents.core.message import Message, MessageRole


class ConversationHistory(BaseModel):
    """
    Manages conversation history with windowing and summarization support.

    Attributes:
        messages: List of messages in the conversation
        max_messages: Maximum number of messages to keep
        max_tokens: Maximum token count (approximate)
        summary: Optional summary of truncated history

    Example:
        >>> history = ConversationHistory(max_messages=100)
        >>> history.add(Message.user("Hello!"))
        >>> history.add(Message.assistant("Hi there!"))
        >>> len(history.messages)
        2
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    messages: list[Message] = Field(default_factory=list)
    max_messages: int | None = None
    max_tokens: int | None = None
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add(self, message: Message) -> None:
        """Add a message to the history."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        self._apply_limits()

    def add_many(self, messages: list[Message]) -> None:
        """Add multiple messages to the history."""
        self.messages.extend(messages)
        self.updated_at = datetime.utcnow()
        self._apply_limits()

    def _apply_limits(self) -> None:
        """Apply message and token limits."""
        if self.max_messages and len(self.messages) > self.max_messages:
            # Keep system messages and recent messages
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]

            keep_count = self.max_messages - len(system_msgs)
            if keep_count > 0:
                self.messages = system_msgs + other_msgs[-keep_count:]
            else:
                self.messages = system_msgs[-self.max_messages:]

    def get_messages(
        self,
        include_system: bool = True,
        last_n: int | None = None
    ) -> list[Message]:
        """Get messages from history."""
        messages = self.messages

        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]

        if last_n is not None:
            messages = messages[-last_n:]

        return messages

    def get_system_message(self) -> Message | None:
        """Get the system message if present."""
        for msg in self.messages:
            if msg.role == MessageRole.SYSTEM:
                return msg
        return None

    def clear(self, keep_system: bool = True) -> None:
        """Clear the conversation history."""
        if keep_system:
            self.messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        else:
            self.messages = []
        self.updated_at = datetime.utcnow()

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Convert messages to list of dictionaries for API calls."""
        return [msg.to_dict() for msg in self.messages]

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)


class AgentContext(BaseModel):
    """
    Context for an agent run, including conversation history and metadata.

    Provides a unified context object that can be passed through the agent
    pipeline and middleware.

    Attributes:
        conversation_id: Unique identifier for the conversation
        user_id: Optional user identifier
        session_id: Optional session identifier
        history: Conversation history
        variables: Custom variables for the agent
        metadata: Additional context metadata
        parent_context: Optional parent context for nested agents

    Example:
        >>> context = AgentContext(user_id="user-123")
        >>> context.set("user_name", "Alice")
        >>> context.history.add(Message.user("Hello!"))
    """

    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str | None = None
    session_id: str | None = None
    history: ConversationHistory = Field(default_factory=ConversationHistory)
    variables: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_context: AgentContext | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    def set(self, key: str, value: Any) -> None:
        """Set a variable in the context."""
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        return self.variables.get(key, default)

    def has(self, key: str) -> bool:
        """Check if a variable exists in the context."""
        return key in self.variables

    def delete(self, key: str) -> None:
        """Delete a variable from the context."""
        self.variables.pop(key, None)

    def child_context(self, **kwargs: Any) -> AgentContext:
        """Create a child context that inherits from this context."""
        return AgentContext(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            session_id=self.session_id,
            history=ConversationHistory(
                messages=list(self.history.messages),
                max_messages=self.history.max_messages,
                max_tokens=self.history.max_tokens,
            ),
            variables=dict(self.variables),
            metadata=dict(self.metadata),
            parent_context=self,
            **kwargs
        )

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history."""
        self.history.add(message)

    def get_messages(self) -> list[Message]:
        """Get all messages from the history."""
        return self.history.get_messages()

    @classmethod
    def from_messages(cls, messages: list[Message], **kwargs: Any) -> AgentContext:
        """Create a context from a list of messages."""
        history = ConversationHistory(messages=messages)
        return cls(history=history, **kwargs)


class ContextManager:
    """
    Manager for agent contexts with persistence support.

    Provides context creation, retrieval, and cleanup operations.
    """

    def __init__(self) -> None:
        self._contexts: dict[str, AgentContext] = {}

    def create(self, **kwargs: Any) -> AgentContext:
        """Create a new context."""
        context = AgentContext(**kwargs)
        self._contexts[context.conversation_id] = context
        return context

    def get(self, conversation_id: str) -> AgentContext | None:
        """Get a context by conversation ID."""
        return self._contexts.get(conversation_id)

    def get_or_create(self, conversation_id: str, **kwargs: Any) -> AgentContext:
        """Get an existing context or create a new one."""
        if conversation_id in self._contexts:
            return self._contexts[conversation_id]

        context = AgentContext(conversation_id=conversation_id, **kwargs)
        self._contexts[conversation_id] = context
        return context

    def delete(self, conversation_id: str) -> bool:
        """Delete a context."""
        if conversation_id in self._contexts:
            del self._contexts[conversation_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all contexts."""
        self._contexts.clear()

    def list_conversations(self) -> list[str]:
        """List all conversation IDs."""
        return list(self._contexts.keys())
