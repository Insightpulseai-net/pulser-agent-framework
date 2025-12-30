"""
Base middleware classes and chain implementation.

Defines the middleware pattern for intercepting agent operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from pulser_agents.core.context import AgentContext
from pulser_agents.core.message import Message
from pulser_agents.core.response import RunResult


class MiddlewareContext(BaseModel):
    """
    Context passed through middleware chain.

    Carries request/response data and allows middleware to
    add metadata and modifications.

    Attributes:
        request_id: Unique request identifier
        agent_name: Name of the agent being called
        input_message: The input message
        context: Agent context
        start_time: When the request started
        metadata: Additional middleware metadata
        response: Response (set by agent or middleware)
        error: Any error that occurred
    """

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str | None = None
    input_message: str | Message | None = None
    context: AgentContext | None = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    response: RunResult | None = None
    error: Exception | None = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)


# Type for the next handler in the chain
NextHandler = Callable[[MiddlewareContext], Any]


class Middleware(ABC):
    """
    Abstract base class for middleware.

    Middleware intercepts agent calls and can:
    - Modify input before processing
    - Modify output after processing
    - Short-circuit processing (e.g., from cache)
    - Add side effects (e.g., logging)

    Example:
        >>> class TimingMiddleware(Middleware):
        ...     async def __call__(
        ...         self,
        ...         ctx: MiddlewareContext,
        ...         next: NextHandler,
        ...     ) -> RunResult:
        ...         start = time.time()
        ...         result = await next(ctx)
        ...         elapsed = time.time() - start
        ...         print(f"Request took {elapsed:.2f}s")
        ...         return result
    """

    @abstractmethod
    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """
        Process the middleware.

        Args:
            ctx: Middleware context with request data
            next_handler: Function to call the next middleware/agent

        Returns:
            The result from the agent or middleware
        """
        pass

    @property
    def name(self) -> str:
        """Get middleware name."""
        return self.__class__.__name__


class MiddlewareChain:
    """
    Chain of middleware to be executed in order.

    Middleware is executed in order for requests and
    reverse order for responses (like an onion).

    Example:
        >>> chain = MiddlewareChain()
        >>> chain.add(LoggingMiddleware())
        >>> chain.add(CacheMiddleware())
        >>> chain.add(RetryMiddleware())
        >>>
        >>> result = await chain.execute(agent.run, ctx)
    """

    def __init__(self) -> None:
        self._middleware: list[Middleware] = []

    def add(self, middleware: Middleware) -> MiddlewareChain:
        """Add middleware to the chain."""
        self._middleware.append(middleware)
        return self

    def remove(self, middleware_type: type) -> bool:
        """Remove middleware by type."""
        for i, mw in enumerate(self._middleware):
            if isinstance(mw, middleware_type):
                self._middleware.pop(i)
                return True
        return False

    def clear(self) -> None:
        """Remove all middleware."""
        self._middleware.clear()

    def __len__(self) -> int:
        return len(self._middleware)

    async def execute(
        self,
        handler: Callable[..., Any],
        ctx: MiddlewareContext,
        *args: Any,
        **kwargs: Any,
    ) -> RunResult:
        """
        Execute the middleware chain with the final handler.

        Args:
            handler: The final handler (usually agent.run)
            ctx: Middleware context
            *args: Arguments for the handler
            **kwargs: Keyword arguments for the handler

        Returns:
            Result from the handler or middleware
        """
        # Build the chain from inside out
        async def final_handler(c: MiddlewareContext) -> RunResult:
            result = await handler(*args, **kwargs)
            c.response = result
            return result

        chain = final_handler

        # Wrap each middleware around the chain
        for middleware in reversed(self._middleware):
            prev_chain = chain

            async def create_handler(mw: Middleware, next_fn: NextHandler):
                async def wrapped(c: MiddlewareContext) -> RunResult:
                    return await mw(c, next_fn)
                return wrapped

            chain = await create_handler(middleware, prev_chain)

        return await chain(ctx)


class MiddlewareStack:
    """
    Alternative middleware implementation using a stack pattern.

    Provides before/after hooks instead of wrapping.

    Example:
        >>> stack = MiddlewareStack()
        >>> stack.before(validate_input)
        >>> stack.after(log_response)
        >>> result = await stack.run(agent.run, message)
    """

    def __init__(self) -> None:
        self._before: list[Callable[[MiddlewareContext], Any]] = []
        self._after: list[Callable[[MiddlewareContext, RunResult], Any]] = []
        self._on_error: list[Callable[[MiddlewareContext, Exception], Any]] = []

    def before(
        self,
        hook: Callable[[MiddlewareContext], Any],
    ) -> MiddlewareStack:
        """Add a before hook."""
        self._before.append(hook)
        return self

    def after(
        self,
        hook: Callable[[MiddlewareContext, RunResult], Any],
    ) -> MiddlewareStack:
        """Add an after hook."""
        self._after.append(hook)
        return self

    def on_error(
        self,
        hook: Callable[[MiddlewareContext, Exception], Any],
    ) -> MiddlewareStack:
        """Add an error hook."""
        self._on_error.append(hook)
        return self

    async def run(
        self,
        handler: Callable[..., Any],
        ctx: MiddlewareContext,
        *args: Any,
        **kwargs: Any,
    ) -> RunResult:
        """Run the handler with before/after hooks."""
        # Run before hooks
        for hook in self._before:
            result = hook(ctx)
            if hasattr(result, "__await__"):
                await result

        try:
            # Run the handler
            result = await handler(*args, **kwargs)
            ctx.response = result

            # Run after hooks
            for hook in self._after:
                hook_result = hook(ctx, result)
                if hasattr(hook_result, "__await__"):
                    await hook_result

            return result

        except Exception as e:
            ctx.error = e

            # Run error hooks
            for hook in self._on_error:
                hook_result = hook(ctx, e)
                if hasattr(hook_result, "__await__"):
                    await hook_result

            raise
