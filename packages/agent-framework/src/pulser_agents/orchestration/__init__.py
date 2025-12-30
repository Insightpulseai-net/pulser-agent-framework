"""
Multi-agent orchestration patterns.

Provides various patterns for coordinating multiple agents including:
- Sequential orchestration
- Concurrent/parallel execution
- Group chat with turn-taking
- Hierarchical delegation
- Handoff patterns
"""

from pulser_agents.orchestration.base import (
    OrchestrationResult,
    Orchestrator,
    OrchestratorConfig,
)
from pulser_agents.orchestration.concurrent import ConcurrentOrchestrator
from pulser_agents.orchestration.group_chat import (
    GroupChatConfig,
    GroupChatOrchestrator,
    SpeakerSelectionMode,
)
from pulser_agents.orchestration.handoff import (
    HandoffOrchestrator,
    HandoffStrategy,
)
from pulser_agents.orchestration.sequential import SequentialOrchestrator

__all__ = [
    "Orchestrator",
    "OrchestratorConfig",
    "OrchestrationResult",
    "SequentialOrchestrator",
    "ConcurrentOrchestrator",
    "GroupChatOrchestrator",
    "GroupChatConfig",
    "SpeakerSelectionMode",
    "HandoffOrchestrator",
    "HandoffStrategy",
]
