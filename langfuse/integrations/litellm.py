"""
LiteLLM → Langfuse Integration

Automatic tracing of LiteLLM requests to Langfuse for observability.
"""

import os
import logging
from typing import Dict, Any, Optional
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiteLLMLangfuseTracer:
    """Trace LiteLLM requests to Langfuse."""

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "http://localhost:3000"
    ):
        self.langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        logger.info(f"Initialized Langfuse tracer: {host}")

    @observe(name="litellm_request")
    async def trace_request(
        self,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trace LiteLLM request to Langfuse.

        Args:
            model: LLM model name
            messages: Chat messages
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            user_id: User identifier
            session_id: Session identifier
            metadata: Additional metadata

        Returns:
            Trace metadata
        """
        # Create generation span
        generation = langfuse_context.get_current_trace().generation(
            name="llm_call",
            model=model,
            input=messages,
            metadata={
                "temperature": temperature,
                "max_tokens": max_tokens,
                **(metadata or {})
            }
        )

        # Set trace attributes
        if user_id:
            langfuse_context.update_current_trace(user_id=user_id)

        if session_id:
            langfuse_context.update_current_trace(session_id=session_id)

        logger.info(f"Created Langfuse trace for {model}")

        return {
            "trace_id": langfuse_context.get_current_trace().id,
            "generation_id": generation.id
        }

    def record_response(
        self,
        trace_id: str,
        generation_id: str,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        latency_ms: int
    ) -> None:
        """
        Record LLM response to Langfuse.

        Args:
            trace_id: Trace ID from trace_request
            generation_id: Generation ID from trace_request
            response: LLM response text
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            cost_usd: Request cost
            latency_ms: Request latency
        """
        # Update generation with response
        generation = self.langfuse.generation(
            id=generation_id,
            output=response,
            usage={
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": prompt_tokens + completion_tokens
            },
            metadata={
                "cost_usd": cost_usd,
                "latency_ms": latency_ms
            }
        )

        # Calculate and record cost
        generation.score(
            name="cost",
            value=cost_usd,
            data_type="NUMERIC"
        )

        # Calculate and record latency
        generation.score(
            name="latency",
            value=latency_ms,
            data_type="NUMERIC"
        )

        logger.info(f"Recorded response to Langfuse: {prompt_tokens + completion_tokens} tokens, ${cost_usd:.4f}, {latency_ms}ms")

    def record_error(
        self,
        trace_id: str,
        generation_id: str,
        error: Exception
    ) -> None:
        """Record LLM error to Langfuse."""
        generation = self.langfuse.generation(
            id=generation_id,
            metadata={
                "error": str(error),
                "error_type": type(error).__name__
            },
            level="ERROR"
        )

        logger.error(f"Recorded error to Langfuse: {error}")

    def add_user_feedback(
        self,
        trace_id: str,
        score: float,
        comment: Optional[str] = None
    ) -> None:
        """
        Add user feedback to a trace.

        Args:
            trace_id: Trace ID
            score: Feedback score (0.0-1.0)
            comment: Optional feedback comment
        """
        self.langfuse.score(
            trace_id=trace_id,
            name="user_feedback",
            value=score,
            comment=comment
        )

        logger.info(f"Added user feedback to trace {trace_id}: {score}")

    def get_trace_url(self, trace_id: str) -> str:
        """Get Langfuse UI URL for a trace."""
        return f"{self.langfuse.host}/trace/{trace_id}"


# Example usage
if __name__ == "__main__":
    import asyncio

    tracer = LiteLLMLangfuseTracer(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-test-123"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-test-123"),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    )

    async def test_trace():
        # Simulate LLM request
        trace_metadata = await tracer.trace_request(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=100,
            user_id="user-123",
            session_id="session-456",
            metadata={"agent": "research"}
        )

        print(f"Trace ID: {trace_metadata['trace_id']}")
        print(f"Generation ID: {trace_metadata['generation_id']}")

        # Simulate response
        tracer.record_response(
            trace_id=trace_metadata['trace_id'],
            generation_id=trace_metadata['generation_id'],
            response="Hi there!",
            prompt_tokens=10,
            completion_tokens=5,
            cost_usd=0.0015,
            latency_ms=350
        )

        # Add user feedback
        tracer.add_user_feedback(
            trace_id=trace_metadata['trace_id'],
            score=0.9,
            comment="Great response!"
        )

        print(f"Trace URL: {tracer.get_trace_url(trace_metadata['trace_id'])}")

    asyncio.run(test_trace())
