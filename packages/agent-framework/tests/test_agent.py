"""
Tests for Agent class and related functionality.
"""


import pytest

from pulser_agents import Agent, AgentConfig
from pulser_agents.core.agent import AgentBuilder, Tool, tool
from pulser_agents.core.base_client import MockChatClient, ToolDefinition
from pulser_agents.core.context import AgentContext
from pulser_agents.core.exceptions import AgentError
from pulser_agents.core.message import Message


class TestTool:
    """Tests for Tool class."""

    def test_create_tool_from_function(self):
        def my_func(name: str, count: int) -> str:
            """A test function."""
            return f"{name}: {count}"

        t = Tool(my_func)
        assert t.name == "my_func"
        assert "test function" in t.description

    def test_tool_parameters_auto_generation(self):
        def my_func(name: str, count: int, flag: bool = False) -> str:
            """A test function."""
            return ""

        t = Tool(my_func)
        params = t.parameters
        assert "name" in params
        assert "count" in params
        assert "flag" in params
        assert params["name"]["type"] == "string"
        assert params["count"]["type"] == "integer"
        assert params["flag"]["type"] == "boolean"

    def test_tool_required_parameters(self):
        def my_func(required: str, optional: str = "default") -> str:
            return ""

        t = Tool(my_func)
        assert "required" in t.required
        assert "optional" not in t.required

    def test_tool_to_definition(self):
        def my_func(arg: str) -> str:
            """Description here."""
            return arg

        t = Tool(my_func)
        definition = t.to_definition()

        assert isinstance(definition, ToolDefinition)
        assert definition.name == "my_func"
        assert definition.description == "Description here."

    @pytest.mark.asyncio
    async def test_tool_execute_sync(self):
        def add(a: int, b: int) -> int:
            return a + b

        t = Tool(add)
        result = await t.execute(a=5, b=3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_tool_execute_async(self):
        async def async_add(a: int, b: int) -> int:
            return a + b

        t = Tool(async_add)
        result = await t.execute(a=5, b=3)
        assert result == 8


class TestToolDecorator:
    """Tests for @tool decorator."""

    def test_basic_decorator(self):
        @tool
        def my_tool(x: str) -> str:
            """My tool description."""
            return x

        assert isinstance(my_tool, Tool)
        assert my_tool.name == "my_tool"

    def test_decorator_with_options(self):
        @tool(name="custom_name", description="Custom description")
        def my_tool(x: str) -> str:
            return x

        assert my_tool.name == "custom_name"
        assert my_tool.description == "Custom description"


class TestAgent:
    """Tests for Agent class."""

    def test_create_agent_with_defaults(self):
        agent = Agent()
        assert agent.name == "agent"
        assert agent.client is None
        assert len(agent.tools) == 0

    def test_create_agent_with_config(self):
        config = AgentConfig(
            name="my-agent",
            description="A test agent",
            system_prompt="You are helpful.",
        )
        agent = Agent(config=config)

        assert agent.name == "my-agent"
        assert agent.config.description == "A test agent"

    def test_register_tool(self):
        agent = Agent()

        @tool
        def test_tool(x: str) -> str:
            return x

        agent.register_tool(test_tool)
        assert "test_tool" in agent.tools

    def test_unregister_tool(self):
        agent = Agent()

        @tool
        def test_tool(x: str) -> str:
            return x

        agent.register_tool(test_tool)
        assert agent.unregister_tool("test_tool") is True
        assert "test_tool" not in agent.tools

    def test_system_message_in_context(self):
        agent = Agent(
            config=AgentConfig(system_prompt="Be helpful."),
        )
        system_msg = agent.context.history.get_system_message()
        assert system_msg is not None
        assert system_msg.text == "Be helpful."

    @pytest.mark.asyncio
    async def test_run_without_client_raises(self):
        agent = Agent()
        with pytest.raises(AgentError, match="No chat client"):
            await agent.run("Hello")

    @pytest.mark.asyncio
    async def test_run_with_mock_client(self):
        client = MockChatClient(responses=["Hello back!"])
        agent = Agent(client=client)

        result = await agent.run("Hello")
        assert result.content == "Hello back!"
        assert result.iterations == 1

    @pytest.mark.asyncio
    async def test_chat_shorthand(self):
        client = MockChatClient(responses=["Quick response"])
        agent = Agent(client=client)

        response = await agent.chat("Hello")
        assert response == "Quick response"

    def test_reset_history(self):
        agent = Agent(config=AgentConfig(system_prompt="System"))
        agent.context.add_message(Message.user("Hello"))
        agent.context.add_message(Message.assistant(content="Hi"))

        agent.reset(keep_system=True)
        assert len(agent.context.history) == 1
        role = agent.context.history.messages[0].role
        assert (role.value if hasattr(role, 'value') else role) == "system"


class TestAgentBuilder:
    """Tests for AgentBuilder class."""

    def test_build_basic_agent(self):
        agent = (
            AgentBuilder()
            .name("test-agent")
            .description("A test agent")
            .build()
        )

        assert agent.name == "test-agent"
        assert agent.config.description == "A test agent"

    def test_build_with_tools(self):
        @tool
        def my_tool(x: str) -> str:
            return x

        agent = (
            AgentBuilder()
            .name("tool-agent")
            .tool(my_tool)
            .build()
        )

        assert "my_tool" in agent.tools

    def test_build_with_client(self):
        client = MockChatClient()
        agent = (
            AgentBuilder()
            .client(client)
            .build()
        )

        assert agent.client == client

    def test_build_with_all_options(self):
        @tool
        def tool1(x: str) -> str:
            return x

        @tool
        def tool2(x: str) -> str:
            return x

        client = MockChatClient()
        ctx = AgentContext(user_id="user-123")

        agent = (
            AgentBuilder()
            .name("full-agent")
            .description("Full featured")
            .system_prompt("Be helpful")
            .max_iterations(20)
            .temperature(0.5)
            .client(client)
            .tools([tool1, tool2])
            .context(ctx)
            .build()
        )

        assert agent.name == "full-agent"
        assert agent.config.max_iterations == 20
        assert agent.config.temperature == 0.5
        assert len(agent.tools) == 2
        assert agent.context.user_id == "user-123"


class TestMockChatClient:
    """Tests for MockChatClient."""

    @pytest.mark.asyncio
    async def test_returns_mock_responses(self):
        client = MockChatClient(responses=["First", "Second", "Third"])

        response1 = await client.chat([Message.user("a")])
        response2 = await client.chat([Message.user("b")])
        response3 = await client.chat([Message.user("c")])

        assert response1.content == "First"
        assert response2.content == "Second"
        assert response3.content == "Third"

    @pytest.mark.asyncio
    async def test_cycles_responses(self):
        client = MockChatClient(responses=["A", "B"])

        await client.chat([Message.user("1")])
        await client.chat([Message.user("2")])
        response = await client.chat([Message.user("3")])

        assert response.content == "A"  # Cycles back

    @pytest.mark.asyncio
    async def test_stream_mock_response(self):
        client = MockChatClient(responses=["Hello World"])

        chunks = []
        async for chunk in client.chat_stream([Message.user("test")]):
            chunks.append(chunk.delta)

        assert "".join(chunks) == "Hello World"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
