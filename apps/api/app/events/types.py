"""Domain Event Types

Enumerates conceptual events for Jenna's multi-module architecture.
"""

from enum import Enum


class DomainEventType(str, Enum):
    """Supported platform event types for AI, agents, tools, memory, and devices."""
    # AI Events
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"

    # Agent Events
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"

    # Tool & MCP Events
    TOOL_REQUESTED = "tool_requested"
    TOOL_COMPLETED = "tool_completed"

    # Memory Events
    MEMORY_CREATED = "memory_created"
    MEMORY_RETRIEVED = "memory_retrieved"

    # Device Events
    DEVICE_CONNECTED = "device_connected"
    DEVICE_EVENT = "device_event"

    # Task Events
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"

    # Multimodal Events
    VOICE_EVENT = "voice_event"
    VISION_EVENT = "vision_event"
