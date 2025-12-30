"""
Sequential orchestrator implementation.

Executes agents in sequence, passing output from one to the next.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pulser_agents.core.agent import Agent
from pulser_agents.core.context import AgentContext
from pulser_agents.core.exceptions import MaxIterationsError, OrchestrationError
from pulser_agents.core.message import Message
from pulser_agents.orchestration.base import (
    OrchestrationResult,
    Orchestrator,
    OrchestratorConfig,
)


class SequentialOrchestrator(Orchestrator):
    """
    Executes agents in sequence.

    Each agent receives the output from the previous agent as input.
    Useful for pipeline-style workflows like:
    - Research -> Write -> Review
    - Plan -> Execute -> Verify

    Example:
        >>> orchestrator = SequentialOrchestrator(
        ...     agents=[researcher, writer, editor],
        ...     config=OrchestratorConfig(name="article-pipeline"),
        ... )
        >>> result = await orchestrator.run("Write about quantum computing")
        >>> print(result.content)
    """

    def __init__(
        self,
        agents: list[Agent],
        config: OrchestratorConfig | None = None,
        transform: Callable[[str, Agent, Agent], str] | None = None,
    ) -> None:
        """
        Initialize the sequential orchestrator.

        Args:
            agents: List of agents to run in sequence
            config: Orchestrator configuration
            transform: Optional function to transform output between agents.
                       Receives (output, current_agent, next_agent) and returns
                       the message for the next agent.
        """
        super().__init__(agents, config)
        self.transform = transform

    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Run agents sequentially.

        Args:
            message: Initial message for the first agent
            context: Optional shared context
            **kwargs: Additional options passed to each agent

        Returns:
            OrchestrationResult with all agent responses
        """
        if not self.agents:
            raise OrchestrationError(
                "No agents configured for sequential orchestration",
                orchestrator=self.name,
            )

        result = self._create_result()
        ctx = context or AgentContext()
        current_input = message if isinstance(message, str) else message.text

        for i, agent in enumerate(self.agents):
            if result.iterations >= self.config.max_iterations:
                raise MaxIterationsError(
                    f"Max iterations ({self.config.max_iterations}) exceeded",
                    max_iterations=self.config.max_iterations,
                    completed_iterations=result.iterations,
                )

            try:
                # Create agent-specific context if preserving history
                if self.config.preserve_history:
                    agent_ctx = ctx.child_context()
                else:
                    agent_ctx = AgentContext()

                # Run the agent
                run_result = await agent.run(current_input, context=agent_ctx, **kwargs)
                response = run_result.final_response

                if response:
                    result.add_turn(agent.name, response)

                    # Prepare input for next agent
                    if i < len(self.agents) - 1:
                        next_agent = self.agents[i + 1]
                        if self.transform:
                            current_input = self.transform(
                                response.content,
                                agent,
                                next_agent,
                            )
                        else:
                            current_input = response.content

            except Exception as e:
                raise OrchestrationError(
                    f"Agent '{agent.name}' failed: {str(e)}",
                    orchestrator=self.name,
                    agents_involved=[a.name for a in self.agents[:i+1]],
                )

        result.complete()
        return result


class PipelineOrchestrator(SequentialOrchestrator):
    """
    Alias for SequentialOrchestrator with pipeline-specific features.

    Adds support for:
    - Named stages
    - Stage-specific configuration
    - Conditional execution
    """

    def __init__(
        self,
        stages: list[tuple[str, Agent]],
        config: OrchestratorConfig | None = None,
        conditions: dict[str, Callable[[str], bool]] | None = None,
    ) -> None:
        """
        Initialize the pipeline orchestrator.

        Args:
            stages: List of (stage_name, agent) tuples
            config: Orchestrator configuration
            conditions: Optional conditions for each stage.
                       If condition returns False, stage is skipped.
        """
        self.stages = stages
        self.conditions = conditions or {}
        agents = [agent for _, agent in stages]
        super().__init__(agents, config)

    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Run the pipeline with conditional stage execution.
        """
        if not self.stages:
            raise OrchestrationError(
                "No stages configured for pipeline",
                orchestrator=self.name,
            )

        result = self._create_result()
        ctx = context or AgentContext()
        current_input = message if isinstance(message, str) else message.text

        for stage_name, agent in self.stages:
            if result.iterations >= self.config.max_iterations:
                raise MaxIterationsError(
                    f"Max iterations ({self.config.max_iterations}) exceeded",
                    max_iterations=self.config.max_iterations,
                    completed_iterations=result.iterations,
                )

            # Check condition for this stage
            if stage_name in self.conditions:
                if not self.conditions[stage_name](current_input):
                    # Skip this stage
                    result.metadata.setdefault("skipped_stages", []).append(stage_name)
                    continue

            try:
                agent_ctx = ctx.child_context() if self.config.preserve_history else AgentContext()
                run_result = await agent.run(current_input, context=agent_ctx, **kwargs)
                response = run_result.final_response

                if response:
                    result.add_turn(agent.name, response)
                    result.metadata.setdefault("completed_stages", []).append(stage_name)
                    current_input = response.content

            except Exception as e:
                raise OrchestrationError(
                    f"Pipeline stage '{stage_name}' (agent: {agent.name}) failed: {str(e)}",
                    orchestrator=self.name,
                    agents_involved=[agent.name],
                )

        result.complete()
        return result
