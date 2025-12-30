"""
Middleware architecture for agents.

Provides extensible middleware for intercepting and modifying
agent behavior including:
- Logging and tracing
- Rate limiting
- Caching
- Validation
- Error handling
"""

from pulser_agents.middleware.base import (
    Middleware,
    MiddlewareChain,
    MiddlewareContext,
)
from pulser_agents.middleware.cache import CacheMiddleware
from pulser_agents.middleware.logging import LoggingMiddleware
from pulser_agents.middleware.rate_limit import RateLimitMiddleware
from pulser_agents.middleware.retry import RetryMiddleware
from pulser_agents.middleware.tracing import TracingMiddleware
from pulser_agents.middleware.validation import (
    InputValidator,
    OutputValidator,
    ValidationMiddleware,
)

__all__ = [
    "Middleware",
    "MiddlewareChain",
    "MiddlewareContext",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "CacheMiddleware",
    "RetryMiddleware",
    "ValidationMiddleware",
    "InputValidator",
    "OutputValidator",
    "TracingMiddleware",
]
