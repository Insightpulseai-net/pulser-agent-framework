"""
Tests for core agent framework components.
"""


import pytest

from pulser_agents.core.context import (
    AgentContext,
    ContextManager,
    ConversationHistory,
)
from pulser_agents.core.exceptions import (
    AgentError,
    ProviderError,
    ToolNotFoundError,
)
from pulser_agents.core.message import (
    Message,
    MessageBuilder,
    MessageRole,
    ToolCall,
)
from pulser_agents.core.response import (
    AgentResponse,
    RunResult,
    Usage,
)


class TestMessage:
    """Tests for Message class."""

    def test_create_user_message(self):
        msg = Message.user("Hello, world!")
        assert msg.role == MessageRole.USER
        assert msg.text == "Hello, world!"

    def test_create_system_message(self):
        msg = Message.system("You are a helpful assistant.")
        assert msg.role == MessageRole.SYSTEM
        assert msg.text == "You are a helpful assistant."

    def test_create_assistant_message(self):
        msg = Message.assistant(content="I'm here to help!")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.text == "I'm here to help!"

    def test_create_tool_result_message(self):
        msg = Message.tool_result(
            tool_call_id="call-123",
            name="get_weather",
            content="Sunny, 72°F",
        )
        assert msg.role == MessageRole.TOOL
        assert msg.text == "Sunny, 72°F"
        assert msg.tool_call_id == "call-123"

    def test_message_to_dict(self):
        msg = Message.user("Hello")
        result = msg.to_dict()
        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_message_with_tool_calls(self):
        tool_calls = [
            ToolCall(id="tc-1", name="get_weather", arguments={"city": "NYC"})
        ]
        msg = Message.assistant(content="", tool_calls=tool_calls)
        assert msg.tool_calls is not None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "get_weather"


class TestMessageBuilder:
    """Tests for MessageBuilder class."""

    def test_build_simple_message(self):
        msg = MessageBuilder().text("Hello").build()
        assert msg.text == "Hello"
        assert msg.role == MessageRole.USER

    def test_build_with_role(self):
        msg = (
            MessageBuilder()
            .role(MessageRole.SYSTEM)
            .text("You are helpful.")
            .build()
        )
        assert msg.role == MessageRole.SYSTEM

    def test_build_with_metadata(self):
        msg = (
            MessageBuilder()
            .text("Hello")
            .metadata("source", "test")
            .build()
        )
        assert msg.metadata["source"] == "test"


class TestConversationHistory:
    """Tests for ConversationHistory class."""

    def test_add_message(self):
        history = ConversationHistory()
        history.add(Message.user("Hello"))
        assert len(history) == 1

    def test_add_many_messages(self):
        history = ConversationHistory()
        history.add_many([
            Message.user("Hello"),
            Message.assistant(content="Hi there!"),
        ])
        assert len(history) == 2

    def test_max_messages_limit(self):
        history = ConversationHistory(max_messages=5)
        for i in range(10):
            history.add(Message.user(f"Message {i}"))
        assert len(history) == 5

    def test_keep_system_messages_on_limit(self):
        history = ConversationHistory(max_messages=3)
        history.add(Message.system("System prompt"))
        for i in range(5):
            history.add(Message.user(f"User {i}"))

        # Should have system message + 2 recent user messages
        assert len(history) == 3
        assert history.messages[0].role == MessageRole.SYSTEM

    def test_get_system_message(self):
        history = ConversationHistory()
        history.add(Message.system("System prompt"))
        history.add(Message.user("Hello"))

        system_msg = history.get_system_message()
        assert system_msg is not None
        assert system_msg.text == "System prompt"

    def test_clear_keep_system(self):
        history = ConversationHistory()
        history.add(Message.system("System"))
        history.add(Message.user("Hello"))
        history.add(Message.assistant(content="Hi"))

        history.clear(keep_system=True)
        assert len(history) == 1
        assert history.messages[0].role == MessageRole.SYSTEM


class TestAgentContext:
    """Tests for AgentContext class."""

    def test_set_and_get_variable(self):
        ctx = AgentContext()
        ctx.set("user_name", "Alice")
        assert ctx.get("user_name") == "Alice"

    def test_get_default_value(self):
        ctx = AgentContext()
        assert ctx.get("missing", "default") == "default"

    def test_has_variable(self):
        ctx = AgentContext()
        ctx.set("key", "value")
        assert ctx.has("key") is True
        assert ctx.has("missing") is False

    def test_delete_variable(self):
        ctx = AgentContext()
        ctx.set("key", "value")
        ctx.delete("key")
        assert ctx.has("key") is False

    def test_child_context(self):
        parent = AgentContext(user_id="user-123")
        parent.set("shared", "value")

        child = parent.child_context()
        assert child.user_id == "user-123"
        assert child.get("shared") == "value"
        assert child.parent_context == parent

    def test_from_messages(self):
        messages = [
            Message.system("System"),
            Message.user("Hello"),
        ]
        ctx = AgentContext.from_messages(messages)
        assert len(ctx.history) == 2


class TestContextManager:
    """Tests for ContextManager class."""

    def test_create_context(self):
        manager = ContextManager()
        ctx = manager.create(user_id="user-123")
        assert ctx.user_id == "user-123"
        assert manager.get(ctx.conversation_id) == ctx

    def test_get_or_create(self):
        manager = ContextManager()
        ctx1 = manager.get_or_create("conv-1")
        ctx2 = manager.get_or_create("conv-1")
        assert ctx1 == ctx2

    def test_delete_context(self):
        manager = ContextManager()
        ctx = manager.create()
        assert manager.delete(ctx.conversation_id) is True
        assert manager.get(ctx.conversation_id) is None

    def test_list_conversations(self):
        manager = ContextManager()
        manager.create()
        manager.create()
        assert len(manager.list_conversations()) == 2


class TestAgentResponse:
    """Tests for AgentResponse class."""

    def test_content_property(self):
        response = AgentResponse(
            message=Message.assistant(content="Hello!"),
        )
        assert response.content == "Hello!"

    def test_has_tool_calls(self):
        response = AgentResponse(
            message=Message.assistant(content=""),
            tool_calls=[ToolCall(name="test", arguments={})],
        )
        assert response.has_tool_calls is True

    def test_to_message(self):
        response = AgentResponse(
            message=Message.assistant(content="Test"),
        )
        msg = response.to_message()
        assert msg.text == "Test"


class TestRunResult:
    """Tests for RunResult class."""

    def test_add_response(self):
        result = RunResult()
        response = AgentResponse(
            message=Message.assistant(content="Test"),
            usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
        result.add_response(response)

        assert result.iterations == 1
        assert result.final_response == response
        assert result.total_usage.total_tokens == 30

    def test_content_property(self):
        result = RunResult()
        result.add_response(AgentResponse(
            message=Message.assistant(content="Final answer"),
        ))
        assert result.content == "Final answer"

    def test_duration(self):
        result = RunResult()
        result.complete()
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0


class TestUsage:
    """Tests for Usage class."""

    def test_cost_estimate(self):
        usage = Usage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        assert abs(usage.cost_estimate - 0.015) < 1e-10  # $0.01 per 1K tokens


class TestExceptions:
    """Tests for exception classes."""

    def test_agent_error(self):
        error = AgentError("Something went wrong", code="ERR001")
        assert str(error) == "[ERR001] Something went wrong"
        assert error.code == "ERR001"

    def test_provider_error(self):
        error = ProviderError(
            "API error",
            provider="openai",
            status_code=500,
        )
        assert error.provider == "openai"
        assert error.status_code == 500

    def test_tool_not_found_error(self):
        error = ToolNotFoundError(
            "Tool not found",
            tool_name="missing_tool",
        )
        assert error.tool_name == "missing_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
