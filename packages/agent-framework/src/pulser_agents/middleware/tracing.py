"""
Tracing middleware for agents.

Provides distributed tracing and observability.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from pulser_agents.core.response import RunResult
from pulser_agents.middleware.base import Middleware, MiddlewareContext, NextHandler


class Span(BaseModel):
    """A span in a distributed trace."""

    trace_id: str
    span_id: str = Field(default_factory=lambda: str(uuid4())[:16])
    parent_span_id: str | None = None
    operation_name: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: str = "ok"
    tags: dict[str, Any] = Field(default_factory=dict)
    logs: list[dict[str, Any]] = Field(default_factory=list)

    def finish(self, status: str = "ok") -> None:
        """Mark the span as finished."""
        self.end_time = datetime.utcnow()
        self.status = status
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def set_tag(self, key: str, value: Any) -> None:
        """Set a tag on the span."""
        self.tags[key] = value

    def log(self, message: str, **kwargs: Any) -> None:
        """Add a log entry to the span."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            **kwargs,
        })


class TraceContext(BaseModel):
    """Context for distributed tracing."""

    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    spans: list[Span] = Field(default_factory=list)
    current_span: Span | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def start_span(
        self,
        operation_name: str,
        parent_span: Span | None = None,
    ) -> Span:
        """Start a new span."""
        span = Span(
            trace_id=self.trace_id,
            operation_name=operation_name,
            parent_span_id=parent_span.span_id if parent_span else None,
        )
        self.spans.append(span)
        self.current_span = span
        return span

    def finish_span(self, status: str = "ok") -> None:
        """Finish the current span."""
        if self.current_span:
            self.current_span.finish(status)

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "trace_id": self.trace_id,
            "spans": [span.model_dump() for span in self.spans],
            "metadata": self.metadata,
        }


class TracingMiddleware(Middleware):
    """
    Middleware for distributed tracing.

    Creates spans for agent requests and integrates with
    tracing systems like OpenTelemetry.

    Example:
        >>> middleware = TracingMiddleware(
        ...     service_name="agent-service",
        ...     exporter=ConsoleExporter(),
        ... )
        >>> chain.add(middleware)
    """

    def __init__(
        self,
        service_name: str = "pulser-agents",
        exporter: Callable[[TraceContext], Any] | None = None,
        sample_rate: float = 1.0,
    ) -> None:
        """
        Initialize tracing middleware.

        Args:
            service_name: Name of the service for spans
            exporter: Function to export traces
            sample_rate: Sampling rate (0.0 to 1.0)
        """
        self.service_name = service_name
        self.exporter = exporter
        self.sample_rate = sample_rate

    def _should_sample(self) -> bool:
        """Determine if this request should be traced."""
        import random
        return random.random() < self.sample_rate

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Create trace span for the request."""
        if not self._should_sample():
            return await next_handler(ctx)

        # Create or get trace context
        trace = ctx.get_metadata("trace_context")
        if not trace:
            trace = TraceContext()
            ctx.set_metadata("trace_context", trace)

        # Start span
        span = trace.start_span(f"agent.{ctx.agent_name or 'unknown'}")
        span.set_tag("service", self.service_name)
        span.set_tag("agent.name", ctx.agent_name)

        if ctx.input_message:
            input_text = (
                ctx.input_message
                if isinstance(ctx.input_message, str)
                else ctx.input_message.text
            )
            span.set_tag("input.length", len(input_text))

        span.log("Request started")

        try:
            result = await next_handler(ctx)

            span.set_tag("iterations", result.iterations)
            if result.total_usage:
                span.set_tag("tokens.total", result.total_usage.total_tokens)

            span.log("Request completed")
            span.finish("ok")

        except Exception as e:
            span.set_tag("error", True)
            span.set_tag("error.type", type(e).__name__)
            span.set_tag("error.message", str(e))
            span.log("Request failed", error=str(e))
            span.finish("error")
            raise

        finally:
            # Export trace
            if self.exporter:
                try:
                    result = self.exporter(trace)
                    if hasattr(result, "__await__"):
                        await result
                except Exception:
                    pass

        return result


class OpenTelemetryMiddleware(Middleware):
    """
    OpenTelemetry integration middleware.

    Integrates with OpenTelemetry for production tracing.

    Example:
        >>> middleware = OpenTelemetryMiddleware(
        ...     service_name="agent-service",
        ... )
    """

    def __init__(
        self,
        service_name: str = "pulser-agents",
    ) -> None:
        self.service_name = service_name
        self._tracer: Any | None = None

    def _get_tracer(self) -> Any:
        """Get or create OpenTelemetry tracer."""
        if self._tracer is None:
            try:
                from opentelemetry import trace
                from opentelemetry.sdk.resources import Resource
                from opentelemetry.sdk.trace import TracerProvider

                resource = Resource.create({"service.name": self.service_name})
                provider = TracerProvider(resource=resource)
                trace.set_tracer_provider(provider)

                self._tracer = trace.get_tracer(__name__)

            except ImportError:
                return None

        return self._tracer

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """Create OpenTelemetry span."""
        tracer = self._get_tracer()

        if tracer is None:
            # OpenTelemetry not available, pass through
            return await next_handler(ctx)

        from opentelemetry.trace import Status, StatusCode

        with tracer.start_as_current_span(
            f"agent.{ctx.agent_name or 'unknown'}",
        ) as span:
            span.set_attribute("agent.name", ctx.agent_name or "unknown")
            span.set_attribute("request.id", ctx.request_id)

            if ctx.input_message:
                input_text = (
                    ctx.input_message
                    if isinstance(ctx.input_message, str)
                    else ctx.input_message.text
                )
                span.set_attribute("input.length", len(input_text))

            try:
                result = await next_handler(ctx)

                span.set_attribute("iterations", result.iterations)
                if result.total_usage:
                    span.set_attribute("tokens.total", result.total_usage.total_tokens)

                span.set_status(Status(StatusCode.OK))
                return result

            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


class ConsoleExporter:
    """Simple console exporter for development."""

    def __call__(self, trace: TraceContext) -> None:
        """Print trace to console."""
        import json
        print("=" * 50)
        print(f"Trace ID: {trace.trace_id}")
        for span in trace.spans:
            print(f"  Span: {span.operation_name}")
            print(f"    Duration: {span.duration_ms:.2f}ms")
            print(f"    Status: {span.status}")
            if span.tags:
                print(f"    Tags: {json.dumps(span.tags)}")
        print("=" * 50)
