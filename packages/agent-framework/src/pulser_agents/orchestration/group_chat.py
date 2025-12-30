"""
Group chat orchestrator implementation.

Enables multi-agent conversations with turn-taking and speaker selection.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from pulser_agents.core.agent import Agent
from pulser_agents.core.context import AgentContext
from pulser_agents.core.exceptions import MaxIterationsError, OrchestrationError
from pulser_agents.core.message import Message
from pulser_agents.orchestration.base import (
    OrchestrationResult,
    Orchestrator,
    OrchestratorConfig,
)


class SpeakerSelectionMode(str, Enum):
    """Mode for selecting the next speaker in group chat."""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    AUTO = "auto"  # LLM-based selection
    MANUAL = "manual"  # Explicit agent selection


class GroupChatConfig(OrchestratorConfig):
    """
    Configuration for group chat orchestration.

    Attributes:
        speaker_selection: Mode for selecting next speaker
        allow_repeat: Whether an agent can speak twice in a row
        termination_phrase: Phrase that ends the conversation
        max_consecutive_auto: Max consecutive auto selections
        admin_name: Name of the admin/moderator
    """

    speaker_selection: SpeakerSelectionMode = SpeakerSelectionMode.AUTO
    allow_repeat: bool = False
    termination_phrase: str | None = "TERMINATE"
    max_consecutive_auto: int = 10
    admin_name: str = "Admin"


class GroupChatMessage(BaseModel):
    """A message in the group chat with speaker info."""

    speaker: str
    content: str
    timestamp: str = Field(default_factory=lambda: str(uuid4())[:8])


class GroupChatOrchestrator(Orchestrator):
    """
    Multi-agent group chat orchestration.

    Agents take turns speaking, with configurable speaker selection
    strategies. Supports round-robin, random, and LLM-based selection.

    Example:
        >>> orchestrator = GroupChatOrchestrator(
        ...     agents=[coder, reviewer, tester],
        ...     config=GroupChatConfig(
        ...         name="dev-team",
        ...         speaker_selection=SpeakerSelectionMode.AUTO,
        ...     ),
        ...     selector_agent=coordinator,
        ... )
        >>> result = await orchestrator.run("Let's build a REST API")
    """

    def __init__(
        self,
        agents: list[Agent],
        config: GroupChatConfig | None = None,
        selector_agent: Agent | None = None,
        termination_func: Callable[[str, int], bool] | None = None,
    ) -> None:
        """
        Initialize the group chat orchestrator.

        Args:
            agents: Agents participating in the chat
            config: Group chat configuration
            selector_agent: Agent for AUTO speaker selection
            termination_func: Custom termination condition.
                            Receives (last_message, turn_count).
        """
        super().__init__(agents, config or GroupChatConfig())
        self.group_config = config or GroupChatConfig()
        self.selector_agent = selector_agent
        self.termination_func = termination_func
        self._chat_history: list[GroupChatMessage] = []
        self._current_speaker_idx = 0

    def _build_chat_context(self) -> str:
        """Build the chat history as context."""
        if not self._chat_history:
            return ""

        lines = []
        for msg in self._chat_history[-20:]:  # Last 20 messages
            lines.append(f"[{msg.speaker}]: {msg.content}")

        return "\n".join(lines)

    def _should_terminate(self, content: str, turn_count: int) -> bool:
        """Check if the conversation should end."""
        if self.termination_func:
            return self.termination_func(content, turn_count)

        if self.group_config.termination_phrase:
            return self.group_config.termination_phrase in content

        return False

    def _get_next_speaker_round_robin(self, last_speaker: str | None) -> Agent:
        """Get next speaker using round-robin."""
        if not self.group_config.allow_repeat and last_speaker:
            # Find last speaker index and move to next
            for i, agent in enumerate(self.agents):
                if agent.name == last_speaker:
                    self._current_speaker_idx = (i + 1) % len(self.agents)
                    break

        agent = self.agents[self._current_speaker_idx]
        self._current_speaker_idx = (self._current_speaker_idx + 1) % len(self.agents)
        return agent

    def _get_next_speaker_random(self, last_speaker: str | None) -> Agent:
        """Get next speaker randomly."""
        import random

        candidates = self.agents
        if not self.group_config.allow_repeat and last_speaker:
            candidates = [a for a in self.agents if a.name != last_speaker]
            if not candidates:
                candidates = self.agents

        return random.choice(candidates)

    async def _get_next_speaker_auto(
        self,
        last_speaker: str | None,
        context: AgentContext,
    ) -> Agent:
        """Get next speaker using LLM selection."""
        if not self.selector_agent:
            # Fallback to round-robin
            return self._get_next_speaker_round_robin(last_speaker)

        # Build selection prompt
        agent_list = "\n".join(
            f"- {a.name}: {a.config.description or 'No description'}"
            for a in self.agents
        )

        chat_context = self._build_chat_context()

        prompt = (
            f"Based on the conversation below, select the most appropriate "
            f"next speaker from the available agents.\n\n"
            f"Available agents:\n{agent_list}\n\n"
            f"Conversation:\n{chat_context}\n\n"
            f"Respond with ONLY the name of the next speaker."
        )

        if not self.group_config.allow_repeat and last_speaker:
            prompt += f"\n\nNote: {last_speaker} just spoke, so select someone else."

        try:
            result = await self.selector_agent.run(prompt, context=context)
            selected_name = result.content.strip()

            # Find the agent
            for agent in self.agents:
                if agent.name.lower() in selected_name.lower():
                    return agent

            # Fallback
            return self._get_next_speaker_round_robin(last_speaker)

        except Exception:
            return self._get_next_speaker_round_robin(last_speaker)

    async def _get_next_speaker(
        self,
        last_speaker: str | None,
        context: AgentContext,
    ) -> Agent:
        """Get the next speaker based on selection mode."""
        mode = self.group_config.speaker_selection

        if mode == SpeakerSelectionMode.ROUND_ROBIN:
            return self._get_next_speaker_round_robin(last_speaker)
        elif mode == SpeakerSelectionMode.RANDOM:
            return self._get_next_speaker_random(last_speaker)
        elif mode == SpeakerSelectionMode.AUTO:
            return await self._get_next_speaker_auto(last_speaker, context)
        else:
            # Manual mode - use round robin as default
            return self._get_next_speaker_round_robin(last_speaker)

    async def run(
        self,
        message: str | Message,
        context: AgentContext | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """
        Run the group chat.

        Args:
            message: Initial message to start the chat
            context: Optional shared context
            **kwargs: Additional options

        Returns:
            OrchestrationResult with all chat turns
        """
        if not self.agents:
            raise OrchestrationError(
                "No agents configured for group chat",
                orchestrator=self.name,
            )

        result = self._create_result()
        ctx = context or AgentContext()
        self._chat_history = []

        # Add initial message from admin
        initial_content = message if isinstance(message, str) else message.text
        self._chat_history.append(GroupChatMessage(
            speaker=self.group_config.admin_name,
            content=initial_content,
        ))

        last_speaker: str | None = None
        turn_count = 0

        while turn_count < self.config.max_iterations:
            turn_count += 1

            if result.iterations >= self.config.max_iterations:
                raise MaxIterationsError(
                    f"Max iterations ({self.config.max_iterations}) exceeded",
                    max_iterations=self.config.max_iterations,
                    completed_iterations=result.iterations,
                )

            # Select next speaker
            speaker = await self._get_next_speaker(last_speaker, ctx)

            # Build context for the speaker
            chat_context = self._build_chat_context()
            agent_prompt = (
                f"You are {speaker.name} in a group conversation.\n"
                f"Here is the conversation so far:\n\n{chat_context}\n\n"
                f"Please provide your response."
            )

            try:
                agent_ctx = ctx.child_context() if self.config.preserve_history else AgentContext()
                run_result = await speaker.run(agent_prompt, context=agent_ctx, **kwargs)
                response = run_result.final_response

                if response:
                    result.add_turn(speaker.name, response)

                    # Add to chat history
                    self._chat_history.append(GroupChatMessage(
                        speaker=speaker.name,
                        content=response.content,
                    ))

                    # Check termination
                    if self._should_terminate(response.content, turn_count):
                        break

                    last_speaker = speaker.name

            except Exception as e:
                raise OrchestrationError(
                    f"Agent '{speaker.name}' failed in group chat: {str(e)}",
                    orchestrator=self.name,
                    agents_involved=[speaker.name],
                )

        result.complete()
        return result

    def get_transcript(self) -> str:
        """Get the full chat transcript."""
        lines = []
        for msg in self._chat_history:
            lines.append(f"[{msg.speaker}]: {msg.content}")
        return "\n\n".join(lines)
