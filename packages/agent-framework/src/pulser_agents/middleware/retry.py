"""
Retry middleware for agents.

Provides automatic retry with backoff for transient failures.
"""

from __future__ import annotations

import asyncio
import random

from pulser_agents.core.exceptions import ProviderError, RateLimitError
from pulser_agents.core.response import RunResult
from pulser_agents.middleware.base import Middleware, MiddlewareContext, NextHandler


class RetryMiddleware(Middleware):
    """
    Middleware for automatic retry with exponential backoff.

    Retries failed requests with configurable backoff strategy
    for handling transient errors.

    Example:
        >>> middleware = RetryMiddleware(
        ...     max_retries=3,
        ...     base_delay=1.0,
        ...     max_delay=60.0,
        ... )
        >>> chain.add(middleware)
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: tuple[type[Exception], ...] | None = None,
        retry_on_status: tuple[int, ...] | None = None,
    ) -> None:
        """
        Initialize retry middleware.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delays
            retry_on: Exception types to retry on
            retry_on_status: HTTP status codes to retry on
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

        self.retry_on = retry_on or (
            ProviderError,
            RateLimitError,
            ConnectionError,
            TimeoutError,
        )

        self.retry_on_status = retry_on_status or (
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay = delay * (0.5 + random.random())

        return delay

    def _should_retry(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry."""
        # Check exception type
        if isinstance(error, self.retry_on):
            return True

        # Check for status code in ProviderError
        if isinstance(error, ProviderError) and error.status_code:
            if error.status_code in self.retry_on_status:
                return True

        return False

    def _get_retry_after(self, error: Exception) -> float | None:
        """Get retry-after from error if available."""
        if isinstance(error, RateLimitError) and error.retry_after:
            return error.retry_after
        return None

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Execute with retry logic."""
        last_error: Exception | None = None
        attempts = 0

        while attempts <= self.max_retries:
            try:
                result = await next_handler(ctx)
                ctx.set_metadata("retry_attempts", attempts)
                return result

            except Exception as e:
                last_error = e
                attempts += 1

                if not self._should_retry(e) or attempts > self.max_retries:
                    ctx.set_metadata("retry_attempts", attempts - 1)
                    ctx.set_metadata("retry_exhausted", True)
                    raise

                # Calculate delay
                retry_after = self._get_retry_after(e)
                delay = retry_after if retry_after else self._calculate_delay(attempts - 1)

                ctx.set_metadata("retry_delay", delay)

                await asyncio.sleep(delay)

        # Should not reach here, but just in case
        if last_error:
            raise last_error

        raise RuntimeError("Retry logic error")


class CircuitBreakerMiddleware(Middleware):
    """
    Circuit breaker pattern for preventing cascade failures.

    Opens the circuit after repeated failures, preventing
    further requests until the circuit resets.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately
    - HALF_OPEN: Testing if service has recovered

    Example:
        >>> middleware = CircuitBreakerMiddleware(
        ...     failure_threshold=5,
        ...     reset_timeout=60.0,
        ... )
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        reset_timeout: float = 60.0,
        failure_on: tuple[type[Exception], ...] | None = None,
    ) -> None:
        """
        Initialize circuit breaker middleware.

        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes to close from half-open
            reset_timeout: Seconds before trying half-open
            failure_on: Exception types that count as failures
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.reset_timeout = reset_timeout
        self.failure_on = failure_on or (
            ProviderError,
            ConnectionError,
            TimeoutError,
        )

        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._lock = asyncio.Lock()

    async def _should_allow_request(self) -> bool:
        """Determine if a request should be allowed."""
        import time

        async with self._lock:
            if self._state == self.CLOSED:
                return True

            if self._state == self.OPEN:
                # Check if reset timeout has elapsed
                if self._last_failure_time:
                    elapsed = time.monotonic() - self._last_failure_time
                    if elapsed >= self.reset_timeout:
                        self._state = self.HALF_OPEN
                        self._success_count = 0
                        return True
                return False

            if self._state == self.HALF_OPEN:
                return True

            return False

    async def _record_success(self) -> None:
        """Record a successful request."""
        async with self._lock:
            if self._state == self.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = self.CLOSED
                    self._failure_count = 0
            elif self._state == self.CLOSED:
                self._failure_count = 0

    async def _record_failure(self) -> None:
        """Record a failed request."""
        import time

        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == self.HALF_OPEN:
                self._state = self.OPEN
            elif self._state == self.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = self.OPEN

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Apply circuit breaker logic."""
        if not await self._should_allow_request():
            ctx.set_metadata("circuit_breaker_state", self._state)
            raise ProviderError(
                "Circuit breaker is open",
                provider="circuit_breaker",
            )

        ctx.set_metadata("circuit_breaker_state", self._state)

        try:
            result = await next_handler(ctx)
            await self._record_success()
            return result

        except Exception as e:
            if isinstance(e, self.failure_on):
                await self._record_failure()
            raise

    def get_state(self) -> dict:
        """Get circuit breaker state."""
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
        }

    async def reset(self) -> None:
        """Manually reset the circuit breaker."""
        async with self._lock:
            self._state = self.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
