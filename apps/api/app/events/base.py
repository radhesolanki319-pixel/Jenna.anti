"""Domain Event Base Contracts

Structured models for event serialization, audit trail integration,
and pub/sub routing across Redis or WebSockets.
"""

from datetime import datetime, timezone
from typing import Any
import uuid
from pydantic import BaseModel, Field

from app.events.types import DomainEventType


class DomainEvent(BaseModel):
    """Standard event envelope used across all Jenna subsystems."""
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: DomainEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: uuid.UUID | None = None
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


# Typed Event Envelopes for Future Domain Specializations
class AIRequestEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.AI_REQUEST


class AIResponseEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.AI_RESPONSE


class AgentStartedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.AGENT_STARTED


class AgentCompletedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.AGENT_COMPLETED


class ToolRequestedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.TOOL_REQUESTED


class ToolCompletedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.TOOL_COMPLETED


class MemoryCreatedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.MEMORY_CREATED


class MemoryRetrievedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.MEMORY_RETRIEVED


class DeviceConnectedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.DEVICE_CONNECTED


class DeviceEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.DEVICE_EVENT


class TaskCreatedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.TASK_CREATED


class TaskCompletedEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.TASK_COMPLETED


class VoiceEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.VOICE_EVENT


class VisionEvent(DomainEvent):
    event_type: DomainEventType = DomainEventType.VISION_EVENT



class DomainEventDispatcher:
    """Dispatches domain events to in-process subscribers and audit systems."""

    def __init__(self) -> None:
        self._subscribers: dict[DomainEventType, list[Any]] = {}

    def subscribe(self, event_type: DomainEventType, handler: Any) -> None:
        """Register a callback for a specific domain event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def dispatch(self, event: DomainEvent) -> None:
        """Dispatch a domain event to all registered subscribers."""
        import asyncio
        import logging
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(handler(event))
                    except RuntimeError:
                        pass
                else:
                    handler(event)
            except Exception as exc:
                logging.getLogger("jenna.events").warning("Domain event handler failed: %s", exc)


domain_dispatcher = DomainEventDispatcher()

