"""
Handoff orchestrator implementation.

Enables dynamic agent handoff based on task requirements.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from pulser_agents.core.agent import Agent
from pulser_agents.core.context import AgentContext
from pulser_agents.core.exceptions import HandoffError, MaxIterationsError, OrchestrationError
from pulser_agents.core.message import Message
from pulser_agents.orchestration.base import (
    OrchestrationResult,
    Orchestrator,
    OrchestratorConfig,
)


class HandoffStrategy(str, Enum):
    """Strategy for determining handoffs."""

    KEYWORD = "keyword"  # Handoff based on keywords
    LLM = "llm"  # LLM-based handoff decision
    EXPLICIT = "explicit"  # Agent explicitly requests handoff
    CONDITION = "condition"  # Custom condition function


class HandoffRule(BaseModel):
    """Rule for when to handoff to a specific agent."""

    target_agent: str
    keywords: list[str] = Field(default_factory=list)
    condition: str | None = None  # Condition description for LLM
    priority: int = 0  # Higher priority rules checked first


class HandoffOrchestrator(Orchestrator):
    """
    Dynamic handoff between agents based on task requirements.

    Agents can hand off work to other agents when:
    - Keywords indicate another agent should handle it
    - An LLM determines handoff is appropriate
    - Agent explicitly requests handoff
    - Custom conditions are met

    Example:
        >>> orchestrator = HandoffOrchestrator(
        ...     agents=[general_agent, code_agent, data_agent],
        ...     router_agent=router,
        ...     rules={
        ...         "code_agent": HandoffRule(
        ...             target_agent="code_agent",
        ...             keywords=["code", "programming", "debug"],
        ...         ),
        ...         "data_agent": HandoffRule(
        ...             target_agent="data_agent",
        ...             keywords=["data", "analysis", "statistics"],
        ...         ),
        ...     },
        ... )
        >>> result = await orchestrator.run("Help me write a Python function")
    """

    def __init__(
        self,
        agents: list[Agent],
        config: OrchestratorConfig | None = None,
        strategy: HandoffStrategy = HandoffStrategy.LLM,
        rules: dict[str, HandoffRule] | None = None,
        router_agent: Agent | None = None,
        default_agent: Agent | None = None,
        handoff_condition: Callable[[str, Agent], Agent | None] | None = None,
    ) -> None:
        """
        Initialize the handoff orchestrator.

        Args:
            agents: Available agents for handoff
            config: Orchestrator configuration
            strategy: Strategy for determining handoffs
            rules: Handoff rules by target agent name
            router_agent: Agent for LLM-based routing
            default_agent: Agent to start with if not specified
            handoff_condition: Custom condition function for CONDITION strategy
        """
        super().__init__(agents, config)
        self.strategy = strategy
        self.rules = rules or {}
        self.router_agent = router_agent
        self.default_agent = default_agent or (agents[0] if agents else None)
        self.handoff_condition = handoff_condition
        self._handoff_history: list[tuple[str, str]] = []

    def _check_keyword_handoff(self, content: str) -> Agent | None:
        """Check if keywords indicate a handoff."""
        content_lower = content.lower()

        # Sort rules by priority
        sorted_rules = sorted(
            self.rules.values(),
            key=lambda r: r.priority,
            reverse=True,
        )

        for rule in sorted_rules:
            for keyword in rule.keywords:
                if keyword.lower() in content_lower:
                    agent = self.get_agent(rule.target_agent)
                    if agent:
                        return agent

        return None

    async def _check_llm_handoff(
        self,
        content: str,
        current_agent: Agent,
        context: AgentContext,
    ) -> Agent | None:
        """Use LLM to determine if handoff is needed."""
        if not self.router_agent:
            return None

        # Build routing prompt
        agent_descriptions = "\n".join(
            f"- {a.name}: {a.config.description or 'General purpose'}"
            for a in self.agents
        )

        prompt = (
            f"Based on the following message, determine if a different agent "
            f"should handle this request.\n\n"
            f"Current agent: {current_agent.name}\n\n"
            f"Available agents:\n{agent_descriptions}\n\n"
            f"Message: {content}\n\n"
            f"If the current agent should continue, respond with 'CONTINUE'.\n"
            f"Otherwise, respond with the name of the agent that should handle this."
        )

        try:
            result = await self.router_agent.run(prompt, context=context)
            response = result.content.strip()

            if response.upper() == "CONTINUE":
                return None

            # Find matching agent
            for agent in self.agents:
                if agent.name.lower() in response.lower():
                    if agent.name != current_agent.name:
                        return agent

            return None

        except Exception:
            return None

    def _check_explicit_handoff(self, content: str) -> tuple[Agent, str] | None:
        """Check if agent explicitly requested handoff."""
        # Look for handoff patterns
        patterns = [
            "handoff to",
            "transfer to",
            "passing to",
            "@handoff",
            "HANDOFF:",
        ]

        content_lower = content.lower()
        for pattern in patterns:
            if pattern in content_lower:
                # Extract target agent name
                idx = content_lower.find(pattern)
                remaining = content[idx + len(pattern):].strip()
                words = remaining.split()

                if words:
                    target_name = words[0].strip("@:,")
                    agent = self.get_agent(target_name)
                    if agent:
                        # Extract reason if provided
                        reason = " ".join(words[1:]) if len(words) > 1 else ""
                        return agent, reason

        return None

    async def _determine_handoff(
        self,
        content: str,
        current_agent: Agent,
        context: AgentContext,
    ) -> Agent | None:
        """Determine if a handoff should occur."""
        if self.strategy == HandoffStrategy.KEYWORD:
            return self._check_keyword_handoff(content)

        elif self.strategy == HandoffStrategy.LLM:
            return await self._check_llm_handoff(content, current_agent, context)

        elif self.strategy == HandoffStrategy.EXPLICIT:
            result = self._check_explicit_handoff(content)
            return result[0] if result else None

        elif self.strategy == HandoffStrategy.CONDITION:
            if self.handoff_condition:
                return self.handoff_condition(content, current_agent)

        return None

    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        start_agent: Agent | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Run the handoff orchestration.

        Args:
            message: Initial message
            context: Optional shared context
            start_agent: Agent to start with (overrides default)
            **kwargs: Additional options

        Returns:
            OrchestrationResult with all agent interactions
        """
        if not self.agents:
            raise OrchestrationError(
                "No agents configured for handoff orchestration",
                orchestrator=self.name,
            )

        result = self._create_result()
        ctx = context or AgentContext()
        self._handoff_history = []

        current_agent = start_agent or self.default_agent
        if not current_agent:
            raise OrchestrationError(
                "No starting agent specified",
                orchestrator=self.name,
            )

        current_input = message if isinstance(message, str) else message.text

        while result.iterations < self.config.max_iterations:
            try:
                agent_ctx = ctx.child_context() if self.config.preserve_history else AgentContext()
                run_result = await current_agent.run(current_input, context=agent_ctx, **kwargs)
                response = run_result.final_response

                if response:
                    result.add_turn(current_agent.name, response)

                    # Check for handoff
                    next_agent = await self._determine_handoff(
                        response.content,
                        current_agent,
                        ctx,
                    )

                    if next_agent:
                        # Record handoff
                        self._handoff_history.append((current_agent.name, next_agent.name))
                        result.metadata.setdefault("handoffs", []).append({
                            "from": current_agent.name,
                            "to": next_agent.name,
                            "turn": result.iterations,
                        })

                        # Prepare input for next agent
                        current_input = (
                            f"[Handoff from {current_agent.name}]\n"
                            f"Context: {response.content}\n"
                            f"Original request: {message if isinstance(message, str) else message.text}"
                        )
                        current_agent = next_agent
                    else:
                        # No handoff, we're done
                        break

            except Exception as e:
                raise HandoffError(
                    f"Agent '{current_agent.name}' failed: {str(e)}",
                    source_agent=self._handoff_history[-1][0] if self._handoff_history else "",
                    target_agent=current_agent.name,
                )

        if result.iterations >= self.config.max_iterations:
            raise MaxIterationsError(
                f"Max iterations ({self.config.max_iterations}) exceeded",
                max_iterations=self.config.max_iterations,
                completed_iterations=result.iterations,
            )

        result.complete()
        return result

    def get_handoff_history(self) -> list[tuple[str, str]]:
        """Get the history of handoffs (source, target) pairs."""
        return list(self._handoff_history)


class SkillBasedRouter(HandoffOrchestrator):
    """
    Specialized handoff orchestrator that routes based on agent skills.

    Each agent declares skills, and the router matches tasks to skills.

    Example:
        >>> router = SkillBasedRouter(
        ...     skill_agents={
        ...         "python": python_agent,
        ...         "javascript": js_agent,
        ...         "database": db_agent,
        ...     },
        ...     router_agent=router,
        ... )
        >>> result = await router.run("Write a SQL query")
    """

    def __init__(
        self,
        skill_agents: dict[str, Agent],
        config: OrchestratorConfig | None = None,
        router_agent: Agent | None = None,
        default_skill: str | None = None,
    ) -> None:
        """
        Initialize the skill-based router.

        Args:
            skill_agents: Mapping of skill names to agents
            config: Orchestrator configuration
            router_agent: Agent for determining required skill
            default_skill: Default skill if none matches
        """
        self.skill_agents = skill_agents
        self.default_skill = default_skill

        agents = list(skill_agents.values())
        super().__init__(
            agents=agents,
            config=config,
            strategy=HandoffStrategy.LLM,
            router_agent=router_agent,
            default_agent=skill_agents.get(default_skill) if default_skill else None,
        )

    async def route(
        self,
        message: str | Message,
        context: AgentContext | None = None,
    ) -> Agent:
        """Determine which agent should handle the message based on skills."""
        if not self.router_agent:
            if self.default_skill and self.default_skill in self.skill_agents:
                return self.skill_agents[self.default_skill]
            return list(self.skill_agents.values())[0]

        ctx = context or AgentContext()
        content = message if isinstance(message, str) else message.text

        skills_list = ", ".join(self.skill_agents.keys())
        prompt = (
            f"Given the following task, determine which skill is most needed.\n\n"
            f"Available skills: {skills_list}\n\n"
            f"Task: {content}\n\n"
            f"Respond with ONLY the skill name that best matches."
        )

        try:
            result = await self.router_agent.run(prompt, context=ctx)
            skill = result.content.strip().lower()

            if skill in self.skill_agents:
                return self.skill_agents[skill]

            # Fuzzy match
            for skill_name, agent in self.skill_agents.items():
                if skill_name in skill or skill in skill_name:
                    return agent

        except Exception:
            pass

        # Fallback
        if self.default_skill and self.default_skill in self.skill_agents:
            return self.skill_agents[self.default_skill]
        return list(self.skill_agents.values())[0]
