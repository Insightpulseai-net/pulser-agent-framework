"""
Logging middleware for agents.

Provides structured logging of agent requests and responses.
"""

from __future__ import annotations

import logging
from typing import Any

from pulser_agents.core.response import RunResult
from pulser_agents.middleware.base import Middleware, MiddlewareContext, NextHandler


class LoggingMiddleware(Middleware):
    """
    Middleware for logging agent interactions.

    Logs request start, completion, and errors with configurable
    detail levels.

    Example:
        >>> middleware = LoggingMiddleware(
        ...     logger=logging.getLogger("agents"),
        ...     log_inputs=True,
        ...     log_outputs=True,
        ... )
        >>> chain.add(middleware)
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        log_inputs: bool = True,
        log_outputs: bool = True,
        log_level: int = logging.INFO,
        truncate_length: int = 500,
    ) -> None:
        """
        Initialize logging middleware.

        Args:
            logger: Logger to use (creates default if None)
            log_inputs: Whether to log input messages
            log_outputs: Whether to log output content
            log_level: Log level for normal operations
            truncate_length: Max length for logged content
        """
        self.logger = logger or logging.getLogger("pulser_agents")
        self.log_inputs = log_inputs
        self.log_outputs = log_outputs
        self.log_level = log_level
        self.truncate_length = truncate_length

    def _truncate(self, text: str) -> str:
        """Truncate text if too long."""
        if len(text) > self.truncate_length:
            return text[:self.truncate_length] + "..."
        return text

    def _format_input(self, ctx: MiddlewareContext) -> str:
        """Format input message for logging."""
        if ctx.input_message is None:
            return "<no input>"

        if isinstance(ctx.input_message, str):
            return self._truncate(ctx.input_message)

        return self._truncate(ctx.input_message.text)

    def _format_output(self, result: RunResult) -> str:
        """Format output for logging."""
        if result.final_response:
            return self._truncate(result.final_response.content)
        return "<no output>"

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Log the request and response."""
        # Log request start
        log_data: dict[str, Any] = {
            "request_id": ctx.request_id,
            "agent": ctx.agent_name,
        }

        if self.log_inputs:
            log_data["input"] = self._format_input(ctx)

        self.logger.log(
            self.log_level,
            "Agent request started",
            extra={"data": log_data},
        )

        try:
            # Call next handler
            result = await next_handler(ctx)

            # Log success
            log_data["elapsed_ms"] = ctx.elapsed_ms
            log_data["iterations"] = result.iterations

            if result.total_usage:
                log_data["tokens"] = result.total_usage.total_tokens

            if self.log_outputs:
                log_data["output"] = self._format_output(result)

            self.logger.log(
                self.log_level,
                "Agent request completed",
                extra={"data": log_data},
            )

            return result

        except Exception as e:
            # Log error
            log_data["elapsed_ms"] = ctx.elapsed_ms
            log_data["error"] = str(e)
            log_data["error_type"] = type(e).__name__

            self.logger.error(
                f"Agent request failed: {e}",
                extra={"data": log_data},
                exc_info=True,
            )

            raise


class StructuredLoggingMiddleware(Middleware):
    """
    Middleware for structured logging using structlog.

    Example:
        >>> import structlog
        >>> middleware = StructuredLoggingMiddleware(
        ...     logger=structlog.get_logger(),
        ... )
    """

    def __init__(
        self,
        logger: Any | None = None,
        log_inputs: bool = True,
        log_outputs: bool = True,
    ) -> None:
        """
        Initialize structured logging middleware.

        Args:
            logger: Structlog logger (creates default if None)
            log_inputs: Whether to log input messages
            log_outputs: Whether to log output content
        """
        if logger is None:
            try:
                import structlog
                self.logger = structlog.get_logger()
            except ImportError:
                # Fallback to standard logging
                self.logger = logging.getLogger("pulser_agents")
        else:
            self.logger = logger

        self.log_inputs = log_inputs
        self.log_outputs = log_outputs

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Log with structured data."""
        bound_logger = self.logger.bind(
            request_id=ctx.request_id,
            agent=ctx.agent_name,
        )

        if self.log_inputs and ctx.input_message:
            input_text = (
                ctx.input_message
                if isinstance(ctx.input_message, str)
                else ctx.input_message.text
            )
            bound_logger = bound_logger.bind(input=input_text[:200])

        bound_logger.info("agent_request_started")

        try:
            result = await next_handler(ctx)

            bound_logger.bind(
                elapsed_ms=ctx.elapsed_ms,
                iterations=result.iterations,
                tokens=result.total_usage.total_tokens if result.total_usage else 0,
            )

            if self.log_outputs and result.final_response:
                bound_logger = bound_logger.bind(
                    output=result.final_response.content[:200]
                )

            bound_logger.info("agent_request_completed")
            return result

        except Exception as e:
            bound_logger.bind(
                elapsed_ms=ctx.elapsed_ms,
                error=str(e),
                error_type=type(e).__name__,
            ).error("agent_request_failed")
            raise
