# Architecture — Jenna Personal AI Platform

> **Status:** Part 1 Foundation (Phases 1–5 Complete)

---

## 1. System Overview

Jenna is a modular, high-reliability personal AI platform structured as a monorepo. The platform enforces strict separation of concerns, asynchronous non-blocking I/O, secure server-side sessions, a 3-tier authorization engine, an automated audit sanitization pipeline, and standardized future domain contracts.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Web Client Browser                             │
│                  Next.js 14 Control Center (Port 3000)                      │
│   ┌─────────────┐  ┌───────────────────┐  ┌─────────────────────────────┐   │
│   │   Sidebar   │  │   Live Telemetry  │  │   Future Module Interfaces  │   │
│   │ Navigation  │  │    Health Grid    │  │  (Chat, Memory, Agents...)  │   │
│   └─────────────┘  └───────────────────┘  └─────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────▲───────────────────┘
                       │ HTTP (REST + Cookies)            │ WebSocket (Duplex)
┌──────────────────────▼──────────────────────────────────┴───────────────────┐
│                           FastAPI Backend (:8000)                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Routers: /health, /auth, /system, /ws                                 │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Services: AuthService, PermissionService (3-Tier), HealthService...   │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Repositories: UserRepo, SessionRepo, AuditRepo (Sanitized), Settings  │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Future Domain Interfaces: AIProvider, Memory, Agent, Tools, Device... │  │
│  │ Domain Events: 14 typed event envelopes for pub/sub & WebSocket       │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
└──────────────────────┬──────────────┴───────────────────┬───────────────────┘
                       │                                  │
┌──────────────────────▼───────┐          ┌───────────────▼───────────────┐
│     PostgreSQL 16 (:5432)    │          │        Redis 7 (:6379)        │
│  - users                     │          │  - Session cache              │
│  - sessions                  │          │  - Sliding window rate limit  │
│  - audit_events (JSONB)      │          │  - Channel pub/sub            │
│  - system_settings           │          │  - Realtime event broker      │
└──────────────────────────────┘          └───────────────────────────────┘
```

---

## 2. Backend Architecture (`apps/api`)

### 2.1 Layer Breakdown

| Directory | Responsibility | Principles |
| :--- | :--- | :--- |
| `app/routers/` | Versioned HTTP & WebSocket route endpoints | Thin handlers; validate inputs via Pydantic; delegate business logic to services. |
| `app/services/` | Platform business logic & domain evaluation | Coordinates repositories, enforces workflows, and handles multi-step actions. |
| `app/repositories/` | Data persistence and query isolation | Extends `BaseRepository[T]`; interacts with PostgreSQL exclusively through async SQLAlchemy sessions. |
| `app/models/` | SQLAlchemy ORM declarative models | Maps relational tables (`users`, `sessions`, `audit_events`, `system_settings`) with UUIDs. |
| `app/schemas/` | Pydantic data validation schemas | Strongly typed request/response contracts with custom validation. |
| `app/interfaces/` | Future domain abstract base classes | Framework-independent abstract base classes for Part 2+ modules (`AIProvider`, `MemoryProvider`, `AgentRunner`, `ToolExecutor`, `DeviceController`, `VisionProvider`, `VoiceProvider`, `TaskScheduler`, `PermissionService`). |
| `app/events/` | Domain event contracts & envelopes | `DomainEvent` base schema with 14 typed lifecycle event variants (`AI_REQUEST`, `AGENT_STARTED`, `TOOL_REQUESTED`, `MEMORY_CREATED`, etc.). |
| `app/core/` | Core configuration, database, Redis, security | Environment settings, PBKDF2 hashing, 3-tier authorization, and database connection pools. |
| `app/websocket/` | Real-time duplex gateway | Manages active WebSocket connections, subscription topics, and ping/pong heartbeats. |

---

## 3. Security & Authorization Architecture

### 3.1 3-Tier Authorization Engine
Authorization decisions evaluate to one of three states:
1. **`ALLOWED`**: Role possesses permission and action is non-sensitive or explicitly authorized.
2. **`DENIED`**: Role lacks the fundamental capability (returns HTTP 403 and records audit event).
3. **`REQUIRES_CONFIRMATION`**: High-risk or sensitive actions (e.g. system wipe, device unlock) prompt for explicit interactive user challenge before execution proceeds.

### 3.2 Recursive Audit Metadata Sanitization
The audit system inspects all metadata JSON dictionaries and scrub strings matching sensitive patterns (`password`, `token`, `secret`, `authorization`, `cookie`, `api_key`, `credential`) to `"[REDACTED]"` before writing to PostgreSQL JSONB storage.

---

## 4. Frontend Architecture (`apps/web`)

### 4.1 Component Hierarchy
- **`DashboardLayout`**: Shared navigation layout providing responsive sidebar, header, theme toggle, and live WebSocket status pill.
- **`Sidebar`**: Accessible navigation covering 10 core routes with phase status badges.
- **`ApiClient`**: Centralized typed HTTP client with automatic cookie transport (`credentials: 'include'`), structured error handling, and 401 redirection callbacks.
- **`useWebSocket`**: Real-time WebSocket hook featuring heartbeat latency measurement and exponential backoff reconnection.
- **`ThemeProvider`**: System, dark, and light theme state management persisted in local preferences.

---

## 5. AI Brain Architecture (`apps/api/app/ai`)

```
               ┌───────────────────────────┐
               │    Chat / API Client      │
               └─────────────┬─────────────┘
                             │ AIRequest
                             ▼
               ┌───────────────────────────┐
               │         AIService         │
               │ - Exponential Backoff     │
               │ - Timeout Enforcement     │
               │ - Token & Latency Logger  │
               │ - Audit Event Dispatcher  │
               └─────────────┬─────────────┘
                             │
                             ▼
               ┌───────────────────────────┐
               │        ModelRouter        │
               │ - Task Type Matching      │
               │ - Capability Filter       │
               │ - Provider Fallback       │
               └───────┬───────────┬───────┘
                       │           │
       ┌───────────────┘           └───────────────┐
       ▼                                           ▼
┌──────────────┐                            ┌──────────────┐
│GeminiProvider│                            │OpenAIProvider│
│google-genai  │                            │    openai    │
└──────────────┘                            └──────────────┘
```

### 5.1 Provider Abstraction & Adapters
- **`BaseAIProvider`**: Common abstract contract requiring `generate()`, `stream()`, `list_models()`, `get_model_info()`, and `health_check()`.
- **`GeminiProvider`**: Adapter utilizing official `google-genai` SDK with real-time streaming, token usage parsing, and error normalization.
- **`OpenAIProvider`**: Adapter utilizing official `openai` SDK with real-time SSE chunk streaming, usage parsing, and error normalization.

### 5.2 Intelligent Model Router & Task Classification
- Supported tasks: `CHAT`, `REASONING`, `CODING`, `ANALYSIS` (with `VISION` and `TOOL_USE` reserved for upcoming phases).
- Dynamic provider failover: If the primary provider encounters an unrecoverable failure or lacks capability, the router gracefully diverts requests to configured fallbacks.

### 5.3 Streaming & Usage Tracking Pipeline
- **SSE Stream (`/api/v1/ai/stream`)**: Pushes discrete events (`stream.started`, `stream.delta`, `stream.completed`, `stream.error`) allowing the UI to render tokens progressively.
- **Usage Database (`ai_usage_logs`)**: Every completion and stream logs prompt tokens, completion tokens, execution latency, provider, model, and correlation IDs in PostgreSQL.

### 5.4 Conversation Engine & Reasoning Pipeline
The conversation engine coordinates multi-turn dialogue with strict user isolation:
```
User Input ──► Context Builder ──► Task Classifier ──► Model Router ──► AI Provider
                     │                                                      │
                     ▼                                                      ▼
             Message Window                                         Response Validator
             & Trim Strategy                                                │
                                                                            ▼
                                                                      SSE Streaming
                                                                            │
                                                                            ▼
                                                                  Database Persistence
                                                              (conversations & messages)
```

- **Task Classifier**: Identifies `CHAT`, `REASONING`, `CODING`, `ANALYSIS`, `RESEARCH`, and `TOOL_REQUEST` without executing unverified tools.
- **Context Builder**: Maintains a sliding window of recent conversation turns (default 20 messages) and provides extension points for future long-term memory, tools, and agent states.
- **Response Validator**: Inspects generated responses to reject empty strings, malformed output, or degenerate repetition loops before writing to PostgreSQL.

### 5.5 Jenna Personality & Multilingual Adaptation
- **Persona**: Confident, empathetic female companion ("Jenna") who is emotionally aware without claiming biological humanity or mimicking proprietary systems.
- **Multilingual Support**: Fluently understands and naturally switches between English, Hindi (Devanagari), and Romanized Hindi (Hinglish).
- **Configuration**: User-specific traits (`personality_style`, `response_style`, `preferred_language`, `verbosity`, `formality`, `humor_level`) persisted in PostgreSQL `system_settings` and layered dynamically into system instructions.

---

## 6. Shared Packages

- **`@jenna/types` (`packages/types`)**: Synchronized TypeScript declarations matching backend Pydantic models, domain event envelopes, AI types (`ChatMessage`, `AIRequest`, `AIResponse`, `AIModelMetadata`, `AIStreamEvent`), memory models (`MemoryRecord`, `MemoryCandidate`, `MemoryStatus`), health responses, and authorization decisions.
- **`@jenna/shared` (`packages/shared`)**: Shared string formatters, time helpers, and configuration constants.

---

## 7. Intelligent Memory Architecture (`apps/api/app/ai/memory`)

> **Security Guarantee:** Memory is strictly user-scoped and sensitive credentials are not stored.

### 7.1 Pipeline & Components
- **`MemoryExtractor`**: Scans conversation turns to extract candidate facts, preferences, personal context, and instructions, separating extraction from persistence.
- **`PrivacyFilter`**: Scans candidates for passwords, API keys, bearer tokens, financial data, and private keys. Default action is `DO NOT STORE`.
- **`MemoryPolicy`**: Evaluates candidates against utility and durability standards, rejecting trivial greetings and small talk.
- **`MemoryDeduplicator`**: Performs semantic and lexical similarity analysis to detect duplicates and contradictory preferences (`CONFLICT`), triggering automatic supersession.
- **`MemoryLifecycleManager`**: Governs state transitions (`CANDIDATE`, `ACTIVE`, `SUPERSEDED`, `ARCHIVED`, `DELETED`) and enforces retention rules (e.g. 7-day temporary expiration, stale archiving).
- **`MemoryContextProvider`**: Injects active, verified memories into prompt context using structured, XML-delimited data framing with prompt-injection defenses.

---

## 8. Specialized Agents & Orchestration Architecture (`apps/api/app/ai/agents`)

```
               ┌────────────────────────────────────────────────────────┐
               │         Client / Orchestrator Web Dashboard            │
               └───────────────────────────┬────────────────────────────┘
                                           │ POST /api/v1/agents/tasks
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                   AgentRunnerService                   │
               │   - User Isolation Check                               │
               │   - 3-Tier Confirmation Enforcement                    │
               │   - Audit Event Dispatcher (DomainEventType)           │
               └─────────────┬────────────────────────────┬─────────────┘
                             │                            │
             (auto_decompose = true)              (execute single task)
                             ▼                            ▼
               ┌───────────────────────────┐┌───────────────────────────┐
               │        TaskPlanner        ││       AgentRegistry       │
               │ - Intent Classification   ││ - RESEARCH (Fact & Search)│
               │ - Bounded Decomposition   ││ - CODING (Refactor & Test)│
               │ - Sequential Subtask Tree ││ - ANALYSIS (Metrics & RCA)│
               │ - Budget Allocation       ││ - WRITING (Docs & Briefs) │
               │                           ││ - GENERAL_TASK (Coord.)   │
               └─────────────┬─────────────┘└─────────────┬─────────────┘
                             │                            │
                             └──────────────┬─────────────┘
                                            ▼
               ┌────────────────────────────────────────────────────────┐
               │              Step-by-Step Execution Loop               │
               │  - Timeout & Cancellation Token Monitoring             │
               │  - Working & Long-Term Memory Context Injection        │
               │  - Telemetry Recording in `agent_step_traces`           │
               │  - Safe Handoff Contract (Zero Chain-of-Thought Leak)  │
               └────────────────────────────────────────────────────────┘
```

### 8.1 Specialized Agent Personas & Registry
- **`ResearchAgent`**: Fact retrieval, technical citations, and literature synthesis. Default budget: 10 steps, 4,000 tokens, 120s timeout.
- **`CodingAgent`**: Code refactoring, test generation, and bug fixing. Default budget: 15 steps, 6,000 tokens, 180s timeout.
- **`AnalysisAgent`**: Root-cause analysis, comparative tradeoffs, and telemetry diagnosis. Default budget: 8 steps, 3,500 tokens, 90s timeout.
- **`WritingAgent`**: Release notes, architectural summaries, and executive briefings. Default budget: 6 steps, 3,000 tokens, 60s timeout.
- **`GeneralTaskAgent`**: Flexible multi-step coordination, triage, and fallback handler. Default budget: 10 steps, 4,000 tokens, 120s timeout.
- **`AgentRegistry`**: Central lookup repository providing capability discovery, default budget instantiation, and runtime registration.

### 8.2 Task Decomposition & Bounded Planning
- **`TaskPlanner`**: Classifies incoming goals and decomposes them into discrete, sequentially ordered subtasks assigned to specialized agent personas.
- **Hard Constraints**: Decomposition enforces strict ceilings (maximum 5 subtasks per plan, maximum 15 execution steps per agent) to prevent infinite loops and runaway costs.
- **Safe Context Handoff**: Inter-agent handoffs pass structured inputs and deliverables (`source_agent`, `task_summary`, `artifacts`, `metadata`) without exposing or storing internal chain-of-thought reasoning.

### 8.3 Persistence, Telemetry & User Isolation
- **`agent_tasks`**: Stores parent tasks and subtasks with lifecycle states (`CREATED`, `QUEUED`, `RUNNING`, `WAITING`, `SUCCEEDED`, `FAILED`, `CANCELLED`), priority levels, budgets, and user foreign keys.
- **`agent_step_traces`**: Records granular per-step telemetry (action, status, duration in milliseconds, output summary, timestamp).
- **3-Tier Interactive Challenges**: Any task involving sensitive actions or external modifications enters `WAITING` status with `requires_confirmation=True`, requiring user approval before execution proceeds.

---

## 9. Tools, Model Context Protocol (MCP) & Web Research Architecture (`apps/api/app/ai/tools`)

```
               ┌────────────────────────────────────────────────────────┐
               │              Agent / Chat / HTTP Client                │
               └───────────────────────────┬────────────────────────────┘
                                           │ POST /api/v1/tools/execute
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                  PlatformToolExecutor                  │
               │   - Schema & Argument Validation                       │
               │   - 3-Tier Authorization (ALLOWED/DENIED/CONFIRMATION) │
               │   - Timeout & Cancellation Token Monitoring            │
               │   - Output Length Truncation Safeguard                 │
               │   - Prompt-Injection Defense Containment Framing       │
               └─────────────┬────────────────────────────┬─────────────┘
                             │                            │
                     (Local Execution)            (Remote MCP Call)
                             ▼                            ▼
               ┌───────────────────────────┐┌───────────────────────────┐
               │    Standard Builtins      ││       MCPClient           │
               │ - calculator (AST Safe)   ││ - Protocol Version        │
               │ - filesystem (Scoped)     ││   2024-11-05              │
               │ - system_info (Telemetry) ││ - JSON-RPC 2.0 Transports │
               │ - web_research (Pipeline) ││ - Dynamic Tool Mapping    │
               └─────────────┬─────────────┘└─────────────┬─────────────┘
                             │                            │
                             └──────────────┬─────────────┘
                                            ▼
               ┌────────────────────────────────────────────────────────┐
               │        <tool_output name="..." status="success">       │
               │  <!-- Untrusted output data framed defensively -->     │
               └────────────────────────────────────────────────────────┘
```

### 9.1 Tool Registry & Builtin Tools
- **`calculator`**: Safe mathematical evaluation using strict Python AST traversal (`ast.parse` and node visitor), preventing arbitrary code execution, division by zero, and unapproved imports.
- **`filesystem_read` & `filesystem_list`**: Directory-scoped file and folder access with strict path traversal defenses rejecting any path escaping the authorized workspace boundary.
- **`filesystem_write`**: Mutating file operations marked `is_sensitive=True` requiring explicit user confirmation before writing.
- **`system_info`**: Safe runtime telemetry (OS, architecture, Python version, uptime) without exposing credentials, keys, or private paths.

### 9.2 Model Context Protocol (MCP) Integration
- Implements current official standard protocol specification (`2024-11-05`).
- **`MCPClient`**: Connects via transports (`MockMCPTransport`, `stdio`, `SSE`), completes `initialize` handshake, dynamically fetches `tools/list`, and maps schemas into native Jenna `ToolDefinitionSchema`.
- Remote tool execution via `tools/call` with error normalization and output bounds.

### 9.3 Web Research Engine & Sourced Synthesis
- **6-Stage Research Workflow**: `search` ➔ `collect sources` ➔ `open/read` ➔ `compare` ➔ `synthesize` ➔ `cite`.
- **`WebContentFetcher`**: HTML parser stripping scripts, styles, and markup with regex-based prompt injection neutralization.
- **Strict Citation Integrity**: Every referenced claim is backed by numbered brackets (`[1]`, `[2]`) linked to verified sources. The system strictly distinguishes sourced facts from inference and never claims a source was read if fetch failed.



