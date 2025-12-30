"""
Exception classes for the Pulser Agent Framework.

All framework exceptions inherit from AgentError for easy catching.
"""

from __future__ import annotations

from typing import Any


class AgentError(Exception):
    """
    Base exception for all agent framework errors.

    Attributes:
        message: Human-readable error message
        code: Optional error code for programmatic handling
        details: Optional dictionary with additional error details
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ProviderError(AgentError):
    """
    Error from an LLM provider (OpenAI, Anthropic, etc.).

    Raised when the provider returns an error or fails to respond.
    """

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: int | None = None,
        response: Any | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.provider = provider
        self.status_code = status_code
        self.response = response


class RateLimitError(ProviderError):
    """Rate limit exceeded from provider."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: float | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, provider, **kwargs)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Authentication failed with provider."""

    pass


class ModelNotFoundError(ProviderError):
    """Requested model not found or not available."""

    pass


class ContextLengthError(ProviderError):
    """Context length exceeded for the model."""

    def __init__(
        self,
        message: str,
        provider: str,
        max_tokens: int | None = None,
        actual_tokens: int | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, provider, **kwargs)
        self.max_tokens = max_tokens
        self.actual_tokens = actual_tokens


class ToolError(AgentError):
    """
    Error during tool/function execution.

    Raised when a tool fails to execute or returns an error.
    """

    def __init__(
        self,
        message: str,
        tool_name: str,
        tool_call_id: str | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.tool_name = tool_name
        self.tool_call_id = tool_call_id


class ToolNotFoundError(ToolError):
    """Requested tool not found."""

    pass


class ToolValidationError(ToolError):
    """Tool arguments failed validation."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        validation_errors: list[dict[str, Any]] | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, tool_name, **kwargs)
        self.validation_errors = validation_errors or []


class ToolExecutionError(ToolError):
    """Tool execution failed."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        original_error: Exception | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, tool_name, **kwargs)
        self.original_error = original_error


class OrchestrationError(AgentError):
    """
    Error during multi-agent orchestration.

    Raised when orchestration fails, such as agent handoff failures
    or group chat coordination errors.
    """

    def __init__(
        self,
        message: str,
        orchestrator: str | None = None,
        agents_involved: list[str] | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.orchestrator = orchestrator
        self.agents_involved = agents_involved or []


class HandoffError(OrchestrationError):
    """Error during agent handoff."""

    def __init__(
        self,
        message: str,
        source_agent: str,
        target_agent: str,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.source_agent = source_agent
        self.target_agent = target_agent


class MaxIterationsError(OrchestrationError):
    """Maximum iterations exceeded in orchestration loop."""

    def __init__(
        self,
        message: str,
        max_iterations: int,
        completed_iterations: int,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.max_iterations = max_iterations
        self.completed_iterations = completed_iterations


class ConfigurationError(AgentError):
    """Error in agent or framework configuration."""

    pass


class MemoryError(AgentError):
    """Error in memory/context operations."""

    pass


class MiddlewareError(AgentError):
    """Error in middleware execution."""

    def __init__(
        self,
        message: str,
        middleware_name: str,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.middleware_name = middleware_name


class StreamingError(AgentError):
    """Error during streaming response."""

    pass


class TimeoutError(AgentError):
    """Operation timed out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds
