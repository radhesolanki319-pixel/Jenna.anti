# Part 2 Implementation Handoff Guide — Jenna Personal AI

> **Status:** Part 1 Foundation is 100% complete, verified, and locked.  
> **Next Step:** Part 2 — Intelligence, Memory, and Agent Implementation.

---

## 1. Executive Summary

Jenna Personal AI's architectural foundation is fully established. All underlying infrastructure—including async PostgreSQL persistence, Redis caching/messaging, server-side secure authentication, 3-tier authorization, audit logging with recursive sanitization, WebSocket communication, and modern Next.js control center dashboard—is production-ready, thoroughly tested, and stabilized.

All contracts and interfaces for future modules in Part 2 and beyond have been defined in `apps/api/app/interfaces/` and mirrored in `packages/types/index.ts`. No mock or pseudo-AI implementations exist; the codebase is cleanly prepared for concrete domain implementations.

---

## 2. Directory Layout & Architecture Reference

```
jenna/
├── apps/
│   ├── api/                     # FastAPI Async Backend (:8000)
│   │   ├── app/
│   │   │   ├── core/            # Config, database, redis, security, permissions
│   │   │   ├── events/          # Domain event envelopes & 14 conceptual types
│   │   │   ├── interfaces/      # Abstract contracts for future modules (Part 2+)
│   │   │   ├── middleware/      # Logging, CORS, error handling
│   │   │   ├── models/          # SQLAlchemy async models (User, Session, Audit, Settings)
│   │   │   ├── repositories/    # Async repository pattern with sanitization
│   │   │   ├── routers/         # Versioned endpoints (/api/v1/health, auth, system)
│   │   │   ├── schemas/         # Pydantic validation schemas
│   │   │   ├── services/        # Business logic & 3-tier permission service
│   │   │   ├── websocket/       # Real-time WebSocket connection manager & dispatch
│   │   │   └── main.py          # FastAPI application entrypoint
│   │   ├── alembic/             # Reversible database migrations
│   │   └── tests/               # Pytest async test suite (100% passing)
│   └── web/                     # Next.js 14 Dashboard (:3000)
│       ├── src/app/             # App Router pages (Home, Chat, Memory, Agents, Settings, Health)
│       ├── src/components/      # Control Center navigation, status indicators, theme
│       ├── src/lib/             # Typed API client with credentials support
│       └── __tests__/           # Jest & React Testing Library test suite
├── packages/
│   ├── shared/                  # Shared constants and utility functions
│   └── types/                   # TypeScript interfaces matching backend models & events
├── infra/docker/                # Docker configuration files
├── docs/                        # Architecture, API, Security, Development, Roadmap
├── docker-compose.yml           # Unified orchestration (web, api, postgres, redis)
└── .env.example                 # Validated environment configuration template
```

---

## 3. Abstract Future Domain Interfaces (`apps/api/app/interfaces/`)

The following abstract base classes are ready for implementation in Part 2:

### 3.1 `AIProvider` (`app.interfaces.ai`)
- **Purpose**: Contract for LLM inference, streaming tokens, and multimodal analysis.
- **Methods**:
  - `generate_text(prompt, context, model, temperature, max_tokens, **kwargs) -> AIGenerationResult`
  - `generate_stream(prompt, context, model, temperature, max_tokens, **kwargs) -> AsyncIterator[str]`
  - `reason_multimodal(prompt, images, model, **kwargs) -> AIGenerationResult`
  - `get_metadata() -> AIProviderMetadata`
- **Part 2 Implementation Target**: Implement Anthropic Claude, OpenAI GPT-4o, or Local Ollama/vLLM providers.

### 3.2 `MemoryProvider` (`app.interfaces.memory`)
- **Purpose**: Unified contract for episodic, working, and semantic vector memory.
- **Methods**:
  - `store(key, content, metadata, user_id) -> MemoryRecord`
  - `retrieve(memory_id) -> MemoryRecord | None`
  - `update(memory_id, content, metadata) -> MemoryRecord`
  - `delete(memory_id) -> bool`
  - `search_semantic(query, limit, threshold, user_id) -> list[MemorySearchResult]`
- **Part 2 Implementation Target**: Connect `pgvector` extension on PostgreSQL or Qdrant/Milvus.

### 3.3 `AgentRunner` (`app.interfaces.agent`)
- **Purpose**: Autonomous goal-driven agents, reasoning loops, and multi-step execution.
- **Methods**:
  - `create_run(agent_name, task, user_id, context) -> AgentRun`
  - `execute_task(run_id) -> AgentTaskResult`
  - `get_status(run_id) -> AgentRun`
  - `cancel_run(run_id) -> bool`
- **Part 2 Implementation Target**: Implement ReAct / Plan-and-Solve agent orchestrator with tool execution.

### 3.4 `ToolExecutor` (`app.interfaces.tools`)
- **Purpose**: Tool registration, schema validation, Model Context Protocol (MCP), and execution.
- **Methods**:
  - `discover_tools() -> list[ToolDefinition]`
  - `validate_call(tool_name, parameters) -> tuple[bool, str | None]`
  - `execute_tool(tool_name, parameters, user_id, permissions) -> ToolResult`
- **Part 2 Implementation Target**: Implement builtin tools (calculator, web search, bash execution) and MCP client.

### 3.5 `DeviceController` (`app.interfaces.device`)
- **Purpose**: Android bridge, hardware telemetry, push notifications, and device commands.
- **Methods**:
  - `list_authorized_devices(user_id) -> list[DeviceMetadata]`
  - `send_command(device_id, command, payload) -> DeviceCommandResult`
  - `receive_event(device_id, event_payload) -> None`
  - `get_device_status(device_id) -> DeviceMetadata`
- **Future Target**: Android companion app WebSocket/WebRTC communication.

### 3.6 `VisionProvider` (`app.interfaces.vision`)
- **Purpose**: Screen inspection, UI element bounding-box detection, and camera sensor context.
- **Methods**:
  - `analyze_image(image_data, prompt) -> VisionAnalysisResult`
  - `analyze_screen(screen_capture, detect_ui_elements) -> VisionAnalysisResult`
  - `get_camera_context() -> CameraContext`

### 3.7 `VoiceProvider` (`app.interfaces.voice`)
- **Purpose**: Speech-to-text (STT), text-to-speech (TTS), and real-time streaming audio pipelines.
- **Methods**:
  - `speech_to_text(audio_data, language) -> AudioTranscription`
  - `stream_speech_to_text(audio_stream, language) -> AsyncIterator[str]`
  - `text_to_speech(text, voice_profile) -> bytes`
  - `stream_text_to_speech(text_stream, voice_profile) -> AsyncIterator[bytes]`

### 3.8 `TaskScheduler` (`app.interfaces.tasks`)
- **Purpose**: Background tasks, cron triggers, and recurring workflow scheduling.
- **Methods**:
  - `schedule_task(task_type, payload, run_at, cron_expression) -> ScheduledTask`
  - `cancel_task(task_id) -> bool`
  - `get_task_status(task_id) -> ScheduledTask | None`
  - `list_pending_tasks(limit) -> list[ScheduledTask]`

---

## 4. Domain Event System (`apps/api/app/events/`)

All domain events inherit from `DomainEvent` with UUID identification, UTC timestamping, and JSON payload serialization:

```python
from app.events import DomainEvent, DomainEventType

event = DomainEvent(
    event_type=DomainEventType.AI_RESPONSE,
    source="llm_service",
    payload={"tokens": 120, "model": "claude-3-7-sonnet"},
)
```

The 14 core event types:
1. `AI_REQUEST` / `AI_RESPONSE`
2. `AGENT_STARTED` / `AGENT_COMPLETED`
3. `TOOL_REQUESTED` / `TOOL_COMPLETED`
4. `MEMORY_CREATED` / `MEMORY_RETRIEVED`
5. `DEVICE_CONNECTED` / `DEVICE_EVENT`
6. `TASK_CREATED` / `TASK_COMPLETED`
7. `VOICE_EVENT` / `VISION_EVENT`

---

## 5. Security & Authorization Ready for Part 2

- **3-Tier Decision Engine**: `PermissionService.evaluate_action()` handles `ALLOWED`, `DENIED`, and `REQUIRES_CONFIRMATION`.
  - When Part 2 tools execute sensitive commands (e.g. `system_reboot`, `file_delete`), the service returns `REQUIRES_CONFIRMATION` until confirmed by the user via WebSocket/UI challenge.
- **Audit Logging**: All actions persist via `AuditEventRepository`, with automated recursive sanitization scrubbing credentials, passwords, and tokens.
- **Role Enforcement**: `admin`, `user`, and `readonly` roles are fully enforced via FastAPI dependencies.

---

## 6. How to Implement a Module in Part 2 (Step-by-Step)

When beginning Part 2 (e.g., implementing `AIProvider`):

1. **Subclass the Interface**:
   ```python
   # apps/api/app/services/ai_provider_impl.py
   from app.interfaces.ai import AIProvider, AIGenerationResult, AIProviderMetadata

   class OpenAIProvider(AIProvider):
       async def generate_text(self, prompt: str, ...) -> AIGenerationResult:
           # Call external provider API
           ...
   ```
2. **Register in Dependency Injection**:
   Create a factory function in `apps/api/app/core/dependencies.py` returning the provider instance.
3. **Connect to Routers**:
   Create `apps/api/app/routers/v1/chat.py` and mount in `apps/api/app/main.py`.
4. **Publish Domain Events**:
   Emit `DomainEventType.AI_REQUEST` and `DomainEventType.AI_RESPONSE` through the event broker.
5. **Connect to Frontend**:
   Update `apps/web/src/app/chat/page.tsx` using `apps/web/src/lib/api.ts` to consume the live endpoint.

---

> **PART 1 FOUNDATION IS FULLY SIGNED OFF AND SEALED.**
