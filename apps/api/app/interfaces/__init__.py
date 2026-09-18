"""Future domain interfaces defining contracts for Part 2 and subsequent phases."""

from app.interfaces.ai import AIGenerationResult, AIProvider, AIProviderMetadata
from app.interfaces.memory import MemoryProvider, MemoryRecord, MemorySearchResult
from app.interfaces.agent import AgentRunner, AgentRun, AgentStatus, AgentTaskResult
from app.interfaces.tools import ToolDefinition, ToolExecutor, ToolParameter, ToolResult
from app.interfaces.device import DeviceCommandResult, DeviceController, DeviceMetadata, DeviceStatus, DeviceType
from app.interfaces.vision import BoundingBox, CameraContext, VisionAnalysisResult, VisionProvider
from app.interfaces.voice import AudioTranscription, VoiceProfile, VoiceProvider
from app.interfaces.permissions import (
    AuthorizationDecision,
    PermissionEvaluationResult,
    PermissionService,
)
from app.interfaces.tasks import ScheduledTask, TaskScheduler, TaskStatus

__all__ = [
    # AI
    "AIProvider",
    "AIProviderMetadata",
    "AIGenerationResult",
    # Memory
    "MemoryProvider",
    "MemoryRecord",
    "MemorySearchResult",
    # Agent
    "AgentRunner",
    "AgentRun",
    "AgentStatus",
    "AgentTaskResult",
    # Tools
    "ToolExecutor",
    "ToolDefinition",
    "ToolParameter",
    "ToolResult",
    # Device
    "DeviceController",
    "DeviceMetadata",
    "DeviceCommandResult",
    "DeviceStatus",
    "DeviceType",
    # Vision
    "VisionProvider",
    "VisionAnalysisResult",
    "BoundingBox",
    "CameraContext",
    # Voice
    "VoiceProvider",
    "AudioTranscription",
    "VoiceProfile",
    # Permissions
    "PermissionService",
    "AuthorizationDecision",
    "PermissionEvaluationResult",
    # Tasks
    "TaskScheduler",
    "ScheduledTask",
    "TaskStatus",
]
