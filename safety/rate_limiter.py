"""
Rate Limiter - Per-user and global rate limiting.

Strategies:
1. Token bucket algorithm
2. Sliding window counter
3. Distributed rate limiting (Redis)
"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from collections import defaultdict
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_hour: int
    burst_size: int
    cost_limit_usd: float


class RateLimiter:
    """Token bucket rate limiter with cost tracking."""

    def __init__(self):
        # Per-user limits
        self.user_limits = {
            "default": RateLimitConfig(
                requests_per_hour=100,
                burst_size=10,
                cost_limit_usd=10.0
            ),
            "premium": RateLimitConfig(
                requests_per_hour=500,
                burst_size=50,
                cost_limit_usd=100.0
            )
        }

        # Global limit
        self.global_limit = RateLimitConfig(
            requests_per_hour=1000,
            burst_size=100,
            cost_limit_usd=500.0
        )

        # Token buckets (user_id -> bucket state)
        self.user_buckets = defaultdict(lambda: {
            "tokens": 100,
            "last_refill": time.time(),
            "cost_today_usd": 0.0
        })

        # Global bucket
        self.global_bucket = {
            "tokens": 1000,
            "last_refill": time.time(),
            "cost_today_usd": 0.0
        }

        # Cost tracking (user_id -> daily cost)
        self.daily_costs = defaultdict(float)
        self.last_cost_reset = time.time()

    async def check_rate_limit(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        user_tier: str = "default"
    ) -> Dict[str, any]:
        """
        Check if request is within rate limits.

        Args:
            user_id: User identifier
            project_id: Project identifier (for project-level limits)
            user_tier: User tier (default, premium)

        Returns:
            Dict with allowed status and metadata
        """
        # Get user config
        user_config = self.user_limits.get(user_tier, self.user_limits["default"])

        # Refill tokens if needed
        self._refill_bucket(user_id, user_config)
        self._refill_global_bucket()

        # Reset daily costs if needed
        self._reset_daily_costs()

        # Check user bucket
        user_bucket = self.user_buckets[user_id]
        if user_bucket["tokens"] < 1:
            return {
                "allowed": False,
                "reason": "user_rate_limit_exceeded",
                "retry_after_seconds": self._calculate_retry_after(user_id, user_config),
                "user_id": user_id,
                "tokens_remaining": 0
            }

        # Check global bucket
        if self.global_bucket["tokens"] < 1:
            return {
                "allowed": False,
                "reason": "global_rate_limit_exceeded",
                "retry_after_seconds": 60,
                "user_id": user_id
            }

        # Check daily cost limit
        user_cost_today = self.daily_costs[user_id]
        if user_cost_today >= user_config.cost_limit_usd:
            return {
                "allowed": False,
                "reason": "daily_cost_limit_exceeded",
                "cost_today_usd": user_cost_today,
                "cost_limit_usd": user_config.cost_limit_usd,
                "user_id": user_id
            }

        # Check global daily cost
        global_cost_today = sum(self.daily_costs.values())
        if global_cost_today >= self.global_limit.cost_limit_usd:
            return {
                "allowed": False,
                "reason": "global_cost_limit_exceeded",
                "cost_today_usd": global_cost_today,
                "cost_limit_usd": self.global_limit.cost_limit_usd
            }

        # Allow request - consume tokens
        user_bucket["tokens"] -= 1
        self.global_bucket["tokens"] -= 1

        return {
            "allowed": True,
            "tokens_remaining": int(user_bucket["tokens"]),
            "global_tokens_remaining": int(self.global_bucket["tokens"]),
            "cost_today_usd": user_cost_today,
            "cost_limit_usd": user_config.cost_limit_usd
        }

    async def record_cost(self, user_id: str, cost_usd: float) -> None:
        """Record cost for a user request."""
        self.daily_costs[user_id] += cost_usd
        self.user_buckets[user_id]["cost_today_usd"] += cost_usd
        self.global_bucket["cost_today_usd"] += cost_usd

        logger.info(f"Recorded cost for {user_id}: ${cost_usd:.4f} (total today: ${self.daily_costs[user_id]:.2f})")

    def _refill_bucket(self, user_id: str, config: RateLimitConfig) -> None:
        """Refill user's token bucket based on elapsed time."""
        bucket = self.user_buckets[user_id]
        now = time.time()
        elapsed = now - bucket["last_refill"]

        # Calculate tokens to add (1 token per 36 seconds for 100/hour)
        tokens_per_second = config.requests_per_hour / 3600.0
        tokens_to_add = elapsed * tokens_per_second

        # Add tokens, capped at burst size
        bucket["tokens"] = min(
            bucket["tokens"] + tokens_to_add,
            config.burst_size
        )
        bucket["last_refill"] = now

    def _refill_global_bucket(self) -> None:
        """Refill global token bucket."""
        now = time.time()
        elapsed = now - self.global_bucket["last_refill"]

        tokens_per_second = self.global_limit.requests_per_hour / 3600.0
        tokens_to_add = elapsed * tokens_per_second

        self.global_bucket["tokens"] = min(
            self.global_bucket["tokens"] + tokens_to_add,
            self.global_limit.burst_size
        )
        self.global_bucket["last_refill"] = now

    def _reset_daily_costs(self) -> None:
        """Reset daily costs at midnight."""
        now = time.time()
        # Check if we've crossed into a new day (86400 seconds = 24 hours)
        if now - self.last_cost_reset >= 86400:
            logger.info("Resetting daily costs")
            self.daily_costs.clear()
            for bucket in self.user_buckets.values():
                bucket["cost_today_usd"] = 0.0
            self.global_bucket["cost_today_usd"] = 0.0
            self.last_cost_reset = now

    def _calculate_retry_after(self, user_id: str, config: RateLimitConfig) -> int:
        """Calculate seconds until next token is available."""
        tokens_per_second = config.requests_per_hour / 3600.0
        seconds_per_token = 1.0 / tokens_per_second
        return int(seconds_per_token) + 1

    def get_user_stats(self, user_id: str) -> Dict[str, any]:
        """Get current rate limit stats for a user."""
        bucket = self.user_buckets[user_id]
        return {
            "user_id": user_id,
            "tokens_remaining": int(bucket["tokens"]),
            "cost_today_usd": self.daily_costs[user_id],
            "last_refill": bucket["last_refill"]
        }

    def get_global_stats(self) -> Dict[str, any]:
        """Get global rate limit stats."""
        return {
            "tokens_remaining": int(self.global_bucket["tokens"]),
            "cost_today_usd": sum(self.daily_costs.values()),
            "total_users": len(self.user_buckets),
            "total_requests_today": sum(100 - int(b["tokens"]) for b in self.user_buckets.values())
        }


async def test_rate_limiter():
    """Test the rate limiter."""
    limiter = RateLimiter()

    print("\n=== Rate Limiter Tests ===\n")

    # Test 1: Normal requests
    print("Test 1: Normal requests (should succeed)")
    for i in range(5):
        result = await limiter.check_rate_limit("user-123")
        print(f"  Request {i+1}: Allowed={result['allowed']}, Tokens={result.get('tokens_remaining', 0)}")

    # Test 2: Burst limit
    print("\nTest 2: Burst limit (exhaust tokens)")
    for i in range(12):
        result = await limiter.check_rate_limit("user-456")
        status = "✓" if result['allowed'] else "✗"
        print(f"  {status} Request {i+1}: {result.get('reason', 'allowed')}")

    # Test 3: Cost tracking
    print("\nTest 3: Cost tracking")
    await limiter.record_cost("user-123", 0.25)
    await limiter.record_cost("user-123", 0.30)
    stats = limiter.get_user_stats("user-123")
    print(f"  User cost: ${stats['cost_today_usd']:.2f}")

    # Test 4: Cost limit
    print("\nTest 4: Cost limit (exceed daily budget)")
    await limiter.record_cost("user-789", 12.0)  # Exceed $10 limit
    result = await limiter.check_rate_limit("user-789")
    print(f"  ✗ Request blocked: {result['reason']}")
    print(f"  Cost today: ${result['cost_today_usd']:.2f} / ${result['cost_limit_usd']:.2f}")

    # Test 5: Global stats
    print("\nTest 5: Global stats")
    global_stats = limiter.get_global_stats()
    print(f"  Global tokens: {global_stats['tokens_remaining']}")
    print(f"  Global cost today: ${global_stats['cost_today_usd']:.2f}")
    print(f"  Total users: {global_stats['total_users']}")


if __name__ == "__main__":
    asyncio.run(test_rate_limiter())
