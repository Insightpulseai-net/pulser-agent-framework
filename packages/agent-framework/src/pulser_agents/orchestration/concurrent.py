"""
Concurrent orchestrator implementation.

Executes multiple agents in parallel and aggregates results.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from pulser_agents.core.agent import Agent
from pulser_agents.core.context import AgentContext
from pulser_agents.core.exceptions import OrchestrationError
from pulser_agents.core.message import Message
from pulser_agents.core.response import AgentResponse
from pulser_agents.orchestration.base import (
    OrchestrationResult,
    Orchestrator,
    OrchestratorConfig,
)

# Type for aggregation functions
AggregationFunc = Callable[[list[AgentResponse]], str]


def default_aggregator(responses: list[AgentResponse]) -> str:
    """Default aggregation: concatenate all responses."""
    return "\n\n---\n\n".join(
        f"**{r.agent_name or 'Agent'}:**\n{r.content}"
        for r in responses
    )


def first_response_aggregator(responses: list[AgentResponse]) -> str:
    """Return only the first response."""
    return responses[0].content if responses else ""


def voting_aggregator(responses: list[AgentResponse]) -> str:
    """Return the most common response (simple voting)."""
    from collections import Counter
    if not responses:
        return ""
    counts = Counter(r.content.strip() for r in responses)
    return counts.most_common(1)[0][0]


class ConcurrentOrchestrator(Orchestrator):
    """
    Executes multiple agents concurrently.

    All agents receive the same input and run in parallel.
    Results are aggregated using a configurable strategy.

    Useful for:
    - Getting multiple perspectives on a problem
    - Ensemble approaches
    - Parallel processing of subtasks

    Example:
        >>> orchestrator = ConcurrentOrchestrator(
        ...     agents=[analyst1, analyst2, analyst3],
        ...     aggregator=voting_aggregator,
        ... )
        >>> result = await orchestrator.run("Analyze this data")
    """

    def __init__(
        self,
        agents: list[Agent],
        config: OrchestratorConfig | None = None,
        aggregator: AggregationFunc | None = None,
        fail_fast: bool = False,
    ) -> None:
        """
        Initialize the concurrent orchestrator.

        Args:
            agents: List of agents to run concurrently
            config: Orchestrator configuration
            aggregator: Function to aggregate responses.
                       Default concatenates all responses.
            fail_fast: If True, cancel remaining agents on first failure
        """
        super().__init__(agents, config)
        self.aggregator = aggregator or default_aggregator
        self.fail_fast = fail_fast

    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Run all agents concurrently.

        Args:
            message: Message sent to all agents
            context: Optional shared context
            **kwargs: Additional options passed to each agent

        Returns:
            OrchestrationResult with aggregated response
        """
        if not self.agents:
            raise OrchestrationError(
                "No agents configured for concurrent orchestration",
                orchestrator=self.name,
            )

        result = self._create_result()
        ctx = context or AgentContext()
        input_msg = message if isinstance(message, str) else message.text

        # Create tasks for all agents
        async def run_agent(agent: Agent) -> tuple[Agent, AgentResponse | None, Exception | None]:
            try:
                agent_ctx = ctx.child_context() if self.config.preserve_history else AgentContext()
                run_result = await agent.run(input_msg, context=agent_ctx, **kwargs)
                return agent, run_result.final_response, None
            except Exception as e:
                return agent, None, e

        tasks = [asyncio.create_task(run_agent(agent)) for agent in self.agents]

        # Handle results
        responses: list[AgentResponse] = []
        errors: list[tuple[str, Exception]] = []

        if self.fail_fast:
            # Cancel all on first error
            try:
                for coro in asyncio.as_completed(tasks):
                    agent, response, error = await coro
                    if error:
                        # Cancel remaining tasks
                        for task in tasks:
                            task.cancel()
                        raise OrchestrationError(
                            f"Agent '{agent.name}' failed: {str(error)}",
                            orchestrator=self.name,
                            agents_involved=[agent.name],
                        )
                    if response:
                        responses.append(response)
                        result.add_turn(agent.name, response)
            except asyncio.CancelledError:
                pass
        else:
            # Gather all results, handling errors
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for item in results:
                if isinstance(item, Exception):
                    errors.append(("unknown", item))
                else:
                    agent, response, error = item
                    if error:
                        errors.append((agent.name, error))
                    elif response:
                        responses.append(response)
                        result.add_turn(agent.name, response)

        if not responses:
            error_details = "; ".join(f"{name}: {str(e)}" for name, e in errors)
            raise OrchestrationError(
                f"All agents failed: {error_details}",
                orchestrator=self.name,
                agents_involved=[name for name, _ in errors],
            )

        # Aggregate responses
        aggregated_content = self.aggregator(responses)

        # Create final aggregated response
        from pulser_agents.core.message import Message as Msg
        final_response = AgentResponse(
            agent_name=self.name,
            message=Msg.assistant(content=aggregated_content),
            usage=result.total_usage,
            finish_reason="aggregated",
            metadata={"errors": [(n, str(e)) for n, e in errors] if errors else []},
        )
        result.final_response = final_response

        result.complete()
        return result


class MapReduceOrchestrator(Orchestrator):
    """
    Map-reduce style orchestration.

    - Map phase: Distribute work to multiple agents in parallel
    - Reduce phase: Aggregate results with a reducer agent

    Example:
        >>> orchestrator = MapReduceOrchestrator(
        ...     mappers=[analyst1, analyst2, analyst3],
        ...     reducer=summarizer_agent,
        ... )
        >>> result = await orchestrator.run("Analyze market trends")
    """

    def __init__(
        self,
        mappers: list[Agent],
        reducer: Agent,
        config: OrchestratorConfig | None = None,
        chunk_func: Callable[[str], list[str]] | None = None,
    ) -> None:
        """
        Initialize the map-reduce orchestrator.

        Args:
            mappers: Agents to process in parallel (map phase)
            reducer: Agent to aggregate results (reduce phase)
            config: Orchestrator configuration
            chunk_func: Optional function to split input into chunks
                       for different mappers. If None, all mappers
                       receive the same input.
        """
        super().__init__(mappers + [reducer], config)
        self.mappers = mappers
        self.reducer = reducer
        self.chunk_func = chunk_func

    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Run map-reduce orchestration.
        """
        result = self._create_result()
        ctx = context or AgentContext()
        input_msg = message if isinstance(message, str) else message.text

        # Map phase
        if self.chunk_func:
            chunks = self.chunk_func(input_msg)
            if len(chunks) != len(self.mappers):
                raise OrchestrationError(
                    f"Chunk function returned {len(chunks)} chunks but "
                    f"there are {len(self.mappers)} mappers",
                    orchestrator=self.name,
                )
            inputs = chunks
        else:
            inputs = [input_msg] * len(self.mappers)

        # Run mappers in parallel
        async def run_mapper(agent: Agent, inp: str) -> tuple[Agent, AgentResponse | None, Exception | None]:
            try:
                agent_ctx = ctx.child_context() if self.config.preserve_history else AgentContext()
                run_result = await agent.run(inp, context=agent_ctx, **kwargs)
                return agent, run_result.final_response, None
            except Exception as e:
                return agent, None, e

        tasks = [
            asyncio.create_task(run_mapper(agent, inp))
            for agent, inp in zip(self.mappers, inputs)
        ]

        mapper_results = await asyncio.gather(*tasks)
        mapper_outputs: list[str] = []

        for agent, response, error in mapper_results:
            if error:
                raise OrchestrationError(
                    f"Mapper '{agent.name}' failed: {str(error)}",
                    orchestrator=self.name,
                    agents_involved=[agent.name],
                )
            if response:
                result.add_turn(agent.name, response)
                mapper_outputs.append(f"[{agent.name}]: {response.content}")

        # Reduce phase
        reduce_input = (
            "Please synthesize the following analyses:\n\n"
            + "\n\n".join(mapper_outputs)
        )

        try:
            reduce_ctx = ctx.child_context() if self.config.preserve_history else AgentContext()
            reduce_result = await self.reducer.run(reduce_input, context=reduce_ctx, **kwargs)
            if reduce_result.final_response:
                result.add_turn(self.reducer.name, reduce_result.final_response)
        except Exception as e:
            raise OrchestrationError(
                f"Reducer '{self.reducer.name}' failed: {str(e)}",
                orchestrator=self.name,
                agents_involved=[self.reducer.name],
            )

        result.complete()
        return result
