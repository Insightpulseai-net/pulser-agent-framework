"""
Rate limiting middleware for agents.

Provides request rate limiting to prevent API overuse.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque

from pulser_agents.core.exceptions import AgentError
from pulser_agents.core.response import RunResult
from pulser_agents.middleware.base import Middleware, MiddlewareContext, NextHandler


class RateLimitExceededError(AgentError):
    """Rate limit has been exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitMiddleware(Middleware):
    """
    Middleware for rate limiting agent requests.

    Implements token bucket algorithm for smooth rate limiting.

    Example:
        >>> middleware = RateLimitMiddleware(
        ...     requests_per_minute=60,
        ...     burst_size=10,
        ... )
        >>> chain.add(middleware)
    """

    def __init__(
        self,
        requests_per_minute: float = 60,
        burst_size: int = 10,
        wait_on_limit: bool = True,
        max_wait_seconds: float = 30.0,
    ) -> None:
        """
        Initialize rate limiting middleware.

        Args:
            requests_per_minute: Sustained request rate
            burst_size: Maximum burst above sustained rate
            wait_on_limit: If True, wait until rate allows; if False, raise error
            max_wait_seconds: Maximum time to wait when wait_on_limit is True
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.wait_on_limit = wait_on_limit
        self.max_wait_seconds = max_wait_seconds

        # Token bucket implementation
        self._tokens = float(burst_size)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

        # Rate per second
        self._rate = requests_per_minute / 60.0

    async def _acquire(self) -> float:
        """
        Acquire a rate limit token.

        Returns wait time in seconds, or raises if limit exceeded.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._last_update = now

            # Add tokens based on elapsed time
            self._tokens = min(
                self.burst_size,
                self._tokens + elapsed * self._rate
            )

            if self._tokens >= 1:
                self._tokens -= 1
                return 0.0

            # Calculate wait time
            wait_time = (1 - self._tokens) / self._rate

            if not self.wait_on_limit:
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Try again in {wait_time:.2f}s",
                    retry_after=wait_time,
                )

            if wait_time > self.max_wait_seconds:
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Required wait ({wait_time:.2f}s) "
                    f"exceeds maximum ({self.max_wait_seconds}s)",
                    retry_after=wait_time,
                )

            return wait_time

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Apply rate limiting to the request."""
        wait_time = await self._acquire()

        if wait_time > 0:
            ctx.set_metadata("rate_limit_wait", wait_time)
            await asyncio.sleep(wait_time)

        return await next_handler(ctx)

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "tokens_available": self._tokens,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size,
        }


class SlidingWindowRateLimiter(Middleware):
    """
    Sliding window rate limiter.

    More accurate than token bucket for strict rate limits.

    Example:
        >>> middleware = SlidingWindowRateLimiter(
        ...     max_requests=100,
        ...     window_seconds=60,
        ... )
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: float = 60.0,
        wait_on_limit: bool = True,
    ) -> None:
        """
        Initialize sliding window rate limiter.

        Args:
            max_requests: Maximum requests in the window
            window_seconds: Window size in seconds
            wait_on_limit: If True, wait for capacity
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.wait_on_limit = wait_on_limit

        self._requests: deque = deque()
        self._lock = asyncio.Lock()

    async def _cleanup(self, now: float) -> None:
        """Remove expired entries from the window."""
        cutoff = now - self.window_seconds
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Apply sliding window rate limiting."""
        async with self._lock:
            now = time.monotonic()
            await self._cleanup(now)

            if len(self._requests) >= self.max_requests:
                if not self.wait_on_limit:
                    oldest = self._requests[0]
                    retry_after = oldest + self.window_seconds - now
                    raise RateLimitExceededError(
                        f"Rate limit exceeded. Try again in {retry_after:.2f}s",
                        retry_after=retry_after,
                    )

                # Wait for oldest request to expire
                oldest = self._requests[0]
                wait_time = oldest + self.window_seconds - now

                if wait_time > 0:
                    ctx.set_metadata("rate_limit_wait", wait_time)
                    # Release lock while waiting
                    self._lock.release()
                    try:
                        await asyncio.sleep(wait_time)
                    finally:
                        await self._lock.acquire()

                    # Cleanup after wait
                    await self._cleanup(time.monotonic())

            self._requests.append(time.monotonic())

        return await next_handler(ctx)
