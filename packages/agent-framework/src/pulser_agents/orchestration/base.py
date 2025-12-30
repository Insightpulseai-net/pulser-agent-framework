"""
Base orchestrator class and common types.

Defines the interface for all orchestration patterns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from pulser_agents.core.agent import Agent
from pulser_agents.core.context import AgentContext
from pulser_agents.core.message import Message
from pulser_agents.core.response import AgentResponse, Usage


class OrchestratorConfig(BaseModel):
    """
    Configuration for orchestrators.

    Attributes:
        name: Orchestrator name for identification
        max_iterations: Maximum number of iterations/turns
        timeout: Maximum time in seconds for orchestration
        preserve_history: Whether to preserve conversation history
        metadata: Additional orchestrator metadata
    """

    name: str = "orchestrator"
    max_iterations: int = 20
    timeout: float | None = None
    preserve_history: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTurn(BaseModel):
    """Record of a single agent turn in orchestration."""

    agent_name: str
    response: AgentResponse
    turn_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OrchestrationResult(BaseModel):
    """
    Result of an orchestration run.

    Attributes:
        id: Unique result identifier
        orchestrator_name: Name of the orchestrator
        turns: List of agent turns
        final_response: The final response from orchestration
        total_usage: Combined token usage
        agents_involved: List of agents that participated
        iterations: Total number of iterations
        started_at: When orchestration started
        completed_at: When orchestration completed
        metadata: Additional result metadata
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    orchestrator_name: str
    turns: list[AgentTurn] = Field(default_factory=list)
    final_response: AgentResponse | None = None
    total_usage: Usage = Field(default_factory=Usage)
    agents_involved: list[str] = Field(default_factory=list)
    iterations: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def content(self) -> str:
        """Get the final response content."""
        if self.final_response:
            return self.final_response.content
        if self.turns:
            return self.turns[-1].response.content
        return ""

    @property
    def all_messages(self) -> list[Message]:
        """Get all messages from all turns."""
        return [turn.response.message for turn in self.turns]

    @property
    def duration_seconds(self) -> float | None:
        """Get orchestration duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def add_turn(self, agent_name: str, response: AgentResponse) -> None:
        """Add a turn to the result."""
        self.turns.append(AgentTurn(
            agent_name=agent_name,
            response=response,
            turn_number=len(self.turns) + 1,
        ))

        if agent_name not in self.agents_involved:
            self.agents_involved.append(agent_name)

        self.total_usage.prompt_tokens += response.usage.prompt_tokens
        self.total_usage.completion_tokens += response.usage.completion_tokens
        self.total_usage.total_tokens += response.usage.total_tokens
        self.iterations += 1

    def complete(self) -> None:
        """Mark orchestration as complete."""
        self.completed_at = datetime.utcnow()
        if self.turns:
            self.final_response = self.turns[-1].response


class Orchestrator(ABC):
    """
    Abstract base class for all orchestrators.

    Orchestrators coordinate multiple agents to accomplish complex tasks
    through various patterns like sequential execution, parallel execution,
    group chat, etc.

    Example:
        >>> orchestrator = SequentialOrchestrator(
        ...     agents=[research_agent, writing_agent, review_agent],
        ... )
        >>> result = await orchestrator.run("Write an article about AI")
    """

    def __init__(
        self,
        agents: list[Agent],
        config: OrchestratorConfig | None = None,
    ) -> None:
        self.agents = agents
        self.config = config or OrchestratorConfig()
        self._agent_map = {agent.name: agent for agent in agents}

    @property
    def name(self) -> str:
        """Get orchestrator name."""
        return self.config.name

    def get_agent(self, name: str) -> Agent | None:
        """Get an agent by name."""
        return self._agent_map.get(name)

    @abstractmethod
    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Run the orchestration.

        Args:
            message: Initial message to start orchestration
            context: Optional shared context
            **kwargs: Additional options

        Returns:
            OrchestrationResult with all turns and final response
        """
        pass

    def _create_result(self) -> OrchestrationResult:
        """Create a new orchestration result."""
        return OrchestrationResult(
            orchestrator_name=self.name,
        )
