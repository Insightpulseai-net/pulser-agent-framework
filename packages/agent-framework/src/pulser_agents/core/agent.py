"""
Base Agent class and configuration.

The Agent is the central abstraction that combines an LLM client with tools,
context management, and middleware to create intelligent conversational agents.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from pulser_agents.core.base_client import BaseChatClient, ToolDefinition
from pulser_agents.core.context import AgentContext
from pulser_agents.core.exceptions import (
    AgentError,
    MaxIterationsError,
    ToolExecutionError,
    ToolNotFoundError,
)
from pulser_agents.core.message import Message, ToolCall
from pulser_agents.core.response import (
    RunResult,
    StreamingResponse,
)


class AgentConfig(BaseModel):
    """
    Configuration for an Agent.

    Attributes:
        name: Agent name for identification
        description: Description of the agent's purpose
        system_prompt: System prompt to set agent behavior
        max_iterations: Maximum tool call iterations per run
        max_tokens: Maximum tokens for responses
        temperature: Sampling temperature
        tools_enabled: Whether tools are enabled
        streaming: Whether to use streaming by default
        metadata: Additional agent metadata

    Example:
        >>> config = AgentConfig(
        ...     name="assistant",
        ...     system_prompt="You are a helpful assistant.",
        ...     max_iterations=10,
        ... )
    """

    name: str = "agent"
    description: str = ""
    system_prompt: str | None = None
    max_iterations: int = 10
    max_tokens: int | None = None
    temperature: float = 0.7
    tools_enabled: bool = True
    streaming: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


# Type alias for tool functions
ToolFunction = Callable[..., Any]


class Tool:
    """
    Wrapper for a tool/function that can be called by the agent.

    Provides automatic schema generation and execution.

    Example:
        >>> @tool
        ... def get_weather(city: str) -> str:
        ...     '''Get the weather for a city.'''
        ...     return f"Weather in {city}: Sunny, 72°F"
    """

    def __init__(
        self,
        func: ToolFunction,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
        required: list[str] | None = None,
    ) -> None:
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self._parameters = parameters
        self._required = required

    @property
    def parameters(self) -> dict[str, Any]:
        """Get the parameter schema for this tool."""
        if self._parameters is not None:
            return self._parameters

        # Auto-generate from function signature
        import inspect
        sig = inspect.signature(self.func)
        params = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                type_map = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                param_type = type_map.get(param.annotation, "string")

            params[param_name] = {"type": param_type}

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        self._parameters = params
        self._required = required
        return params

    @property
    def required(self) -> list[str]:
        """Get the required parameters."""
        if self._required is None:
            # Trigger parameter generation
            _ = self.parameters
        return self._required or []

    def to_definition(self) -> ToolDefinition:
        """Convert to ToolDefinition for the LLM."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            required=self.required,
        )

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments."""
        import asyncio
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        return self.func(**kwargs)


def tool(
    func: ToolFunction | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Tool | Callable[[ToolFunction], Tool]:
    """
    Decorator to create a Tool from a function.

    Example:
        >>> @tool
        ... def search(query: str) -> str:
        ...     '''Search for information.'''
        ...     return f"Results for: {query}"

        >>> @tool(name="calculator", description="Perform calculations")
        ... def calc(expression: str) -> str:
        ...     return str(eval(expression))
    """
    def decorator(f: ToolFunction) -> Tool:
        return Tool(f, name=name, description=description)

    if func is not None:
        return decorator(func)
    return decorator


class Agent:
    """
    The main Agent class that orchestrates LLM interactions.

    An Agent combines a chat client with tools, context management, and
    middleware to create an intelligent conversational agent.

    Attributes:
        config: Agent configuration
        client: The LLM chat client
        tools: Dictionary of available tools
        context: Current agent context
        middleware: List of middleware functions

    Example:
        >>> from pulser_agents import Agent, AgentConfig
        >>> from pulser_agents.providers import OpenAIChatClient
        >>>
        >>> agent = Agent(
        ...     config=AgentConfig(
        ...         name="assistant",
        ...         system_prompt="You are a helpful assistant.",
        ...     ),
        ...     client=OpenAIChatClient(),
        ... )
        >>>
        >>> response = await agent.run("Hello!")
        >>> print(response.content)
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        client: BaseChatClient | None = None,
        tools: list[Tool] | None = None,
        context: AgentContext | None = None,
    ) -> None:
        self.config = config or AgentConfig()
        self.client = client
        self._tools: dict[str, Tool] = {}
        self.context = context or AgentContext()
        self._middleware: list[Callable] = []

        # Register tools
        if tools:
            for t in tools:
                self.register_tool(t)

        # Set up system prompt
        if self.config.system_prompt:
            self._ensure_system_message()

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self.config.name

    @property
    def tools(self) -> dict[str, Tool]:
        """Get registered tools."""
        return self._tools

    def _ensure_system_message(self) -> None:
        """Ensure the system message is in the context."""
        if self.config.system_prompt:
            existing = self.context.history.get_system_message()
            if not existing:
                self.context.history.messages.insert(
                    0,
                    Message.system(self.config.system_prompt)
                )

    def register_tool(self, t: Tool | ToolFunction) -> None:
        """Register a tool with the agent."""
        if not isinstance(t, Tool):
            t = Tool(t)
        self._tools[t.name] = t

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the agent."""
        self._middleware.append(middleware)

    def _get_tool_definitions(self) -> list[ToolDefinition]:
        """Get tool definitions for the LLM."""
        if not self.config.tools_enabled:
            return []
        return [t.to_definition() for t in self._tools.values()]

    async def _execute_tool(self, tool_call: ToolCall) -> Message:
        """Execute a tool call and return the result message."""
        tool = self._tools.get(tool_call.name)
        if not tool:
            raise ToolNotFoundError(
                f"Tool '{tool_call.name}' not found",
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
            )

        try:
            result = await tool.execute(**tool_call.arguments)
            return Message.tool_result(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=str(result),
            )
        except Exception as e:
            raise ToolExecutionError(
                f"Tool '{tool_call.name}' failed: {str(e)}",
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
                original_error=e,
            )

    async def _execute_tools(self, tool_calls: list[ToolCall]) -> list[Message]:
        """Execute multiple tool calls in parallel."""
        tasks = [self._execute_tool(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        messages = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error message for failed tool
                tc = tool_calls[i]
                messages.append(Message.tool_result(
                    tool_call_id=tc.id,
                    name=tc.name,
                    content=f"Error: {str(result)}",
                    is_error=True,
                ))
            else:
                messages.append(result)

        return messages

    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> RunResult:
        """
        Run the agent with a message.

        Handles tool calls automatically, iterating until the model
        stops calling tools or max_iterations is reached.

        Args:
            message: User message or Message object
            context: Optional context override
            **kwargs: Additional options passed to the client

        Returns:
            RunResult with all responses and final result
        """
        if self.client is None:
            raise AgentError("No chat client configured")

        ctx = context or self.context
        result = RunResult(agent_name=self.name)

        # Add user message
        if isinstance(message, str):
            message = Message.user(message)
        ctx.add_message(message)

        tools = self._get_tool_definitions()
        iteration = 0

        while iteration < self.config.max_iterations:
            iteration += 1

            # Get response from LLM
            response = await self.client.chat(
                messages=ctx.get_messages(),
                tools=tools if tools else None,
                **kwargs,
            )
            response.agent_name = self.name

            # Add response to history and result
            ctx.add_message(response.message)
            result.add_response(response)

            # Check for tool calls
            if response.has_tool_calls and response.tool_calls:
                # Execute tools
                tool_messages = await self._execute_tools(response.tool_calls)
                for msg in tool_messages:
                    ctx.add_message(msg)
            else:
                # No tool calls, we're done
                break
        else:
            raise MaxIterationsError(
                f"Max iterations ({self.config.max_iterations}) exceeded",
                max_iterations=self.config.max_iterations,
                completed_iterations=iteration,
            )

        result.complete()
        return result

    async def run_stream(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> StreamingResponse:
        """
        Run the agent with streaming response.

        Note: Tool calls are not automatically handled in streaming mode.
        Use run() for automatic tool handling.

        Args:
            message: User message or Message object
            context: Optional context override
            **kwargs: Additional options passed to the client

        Returns:
            StreamingResponse that can be iterated
        """
        if self.client is None:
            raise AgentError("No chat client configured")

        ctx = context or self.context

        # Add user message
        if isinstance(message, str):
            message = Message.user(message)
        ctx.add_message(message)

        tools = self._get_tool_definitions()

        stream = self.client.chat_stream(
            messages=ctx.get_messages(),
            tools=tools if tools else None,
            **kwargs,
        )

        return StreamingResponse(
            stream=stream,
            agent_name=self.name,
            model=self.client.model,
        )

    async def chat(
        self,
        message: str | Message,
        **kwargs: Any,
    ) -> str:
        """
        Simple chat interface that returns just the response text.

        Args:
            message: User message
            **kwargs: Additional options

        Returns:
            The response text
        """
        result = await self.run(message, **kwargs)
        return result.content

    def reset(self, keep_system: bool = True) -> None:
        """Reset the agent's conversation history."""
        self.context.history.clear(keep_system=keep_system)

    async def close(self) -> None:
        """Close the agent and release resources."""
        if self.client:
            await self.client.close()

    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


class AgentBuilder:
    """
    Builder for creating agents with fluent API.

    Example:
        >>> agent = (AgentBuilder()
        ...     .name("assistant")
        ...     .system_prompt("You are helpful.")
        ...     .client(OpenAIChatClient())
        ...     .tool(search_tool)
        ...     .build())
    """

    def __init__(self) -> None:
        self._config = AgentConfig()
        self._client: BaseChatClient | None = None
        self._tools: list[Tool] = []
        self._context: AgentContext | None = None

    def name(self, name: str) -> AgentBuilder:
        """Set the agent name."""
        self._config.name = name
        return self

    def description(self, description: str) -> AgentBuilder:
        """Set the agent description."""
        self._config.description = description
        return self

    def system_prompt(self, prompt: str) -> AgentBuilder:
        """Set the system prompt."""
        self._config.system_prompt = prompt
        return self

    def max_iterations(self, max_iter: int) -> AgentBuilder:
        """Set max tool call iterations."""
        self._config.max_iterations = max_iter
        return self

    def temperature(self, temp: float) -> AgentBuilder:
        """Set the temperature."""
        self._config.temperature = temp
        return self

    def client(self, client: BaseChatClient) -> AgentBuilder:
        """Set the chat client."""
        self._client = client
        return self

    def tool(self, t: Tool | ToolFunction) -> AgentBuilder:
        """Add a tool."""
        if not isinstance(t, Tool):
            t = Tool(t)
        self._tools.append(t)
        return self

    def tools(self, tools: list[Tool | ToolFunction]) -> AgentBuilder:
        """Add multiple tools."""
        for t in tools:
            self.tool(t)
        return self

    def context(self, context: AgentContext) -> AgentBuilder:
        """Set the context."""
        self._context = context
        return self

    def build(self) -> Agent:
        """Build the agent."""
        return Agent(
            config=self._config,
            client=self._client,
            tools=self._tools,
            context=self._context,
        )
