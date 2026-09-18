# API Reference — Jenna Personal AI Platform

> Version: 0.2.0 | Phase 2: Backend Core + Database

This document details the REST and WebSocket endpoints provided by the Jenna API (`apps/api`).

---

## Architecture & Conventions

- **Base URL**: `http://localhost:8000/api/v1`
- **Documentation**:
  - Swagger UI: `http://localhost:8000/api/docs`
  - ReDoc: `http://localhost:8000/api/redoc`
  - OpenAPI Spec: `http://localhost:8000/api/openapi.json`
- **Correlation & Tracing**:
  - Every request supports or generates an `X-Request-ID` header.
  - The ID is tracked across structured server logs and returned in responses.

---

## Standard Error Response

Centralized error handling returns structured JSON for all exceptions:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {},
    "request_id": "2eab0f01-fd70-41a8-a3fa-7665e65c9d5f",
    "timestamp": "2026-09-12T16:45:42.421886+00:00"
  }
}
```

### Standard Error Codes

| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `UNAUTHORIZED` | `401 Unauthorized` | Missing, invalid, or expired session authentication |
| `FORBIDDEN` | `403 Forbidden` | Authenticated user lacks required platform permissions |
| `VALIDATION_ERROR` | `422 Unprocessable Content` | Request schema or parameter validation failure |
| `NOT_FOUND` | `404 Not Found` | Requested route or database entity does not exist |
| `CONFLICT` | `409 Conflict` | Unique constraint or state conflict |
| `DEPENDENCY_ERROR`| `503 Service Unavailable` | Downstream dependency (PostgreSQL, Redis) failed |
| `INTERNAL_ERROR` | `500 Internal Server Error`| Unexpected server error (stack trace hidden in production) |

---

## REST Endpoints

### 1. Authentication & Session Security

#### `POST /api/v1/auth/register`
Creates a new user account and sets a cryptographically secure HttpOnly cookie (`jenna_session`). The first user registered in the system is automatically designated as `admin`.

**Request Body**:
```json
{
  "email": "admin@jenna.ai",
  "password": "SuperSecretPassword123!"
}
```

**Response `201 Created`**:
```json
{
  "status": "ok",
  "message": "Registration successful",
  "user": {
    "id": "04f1655f-e09b-4d49-a662-0cc3d6ebaf0f",
    "email": "admin@jenna.ai",
    "role": "admin",
    "created_at": "2026-09-12T17:27:52.123067Z"
  }
}
```

#### `POST /api/v1/auth/login`
Authenticates credentials with constant-time PBKDF2 hash verification, generates a high-entropy 32-byte session token, stores the SHA-256 hash in PostgreSQL, and sets the HttpOnly cookie.

**Request Body**:
```json
{
  "email": "admin@jenna.ai",
  "password": "SuperSecretPassword123!"
}
```

**Response `200 OK`**:
```json
{
  "status": "ok",
  "message": "Login successful",
  "user": {
    "id": "04f1655f-e09b-4d49-a662-0cc3d6ebaf0f",
    "email": "admin@jenna.ai",
    "role": "admin",
    "created_at": "2026-09-12T17:27:52.123067Z"
  }
}
```

#### `GET /api/v1/auth/me`
Protected endpoint returning profile metadata, active session expiration, and role permissions. Accepts either `jenna_session` cookie or `Authorization: Bearer <token>` header.

**Response `200 OK`**:
```json
{
  "user": {
    "id": "04f1655f-e09b-4d49-a662-0cc3d6ebaf0f",
    "email": "admin@jenna.ai",
    "role": "admin",
    "created_at": "2026-09-12T17:27:52.123067Z"
  },
  "session": {
    "id": "69ba3c56-75ab-4769-b891-96c6463f7eed",
    "created_at": "2026-09-12T17:29:41.217708Z",
    "expires_at": "2026-09-19T17:29:41.356965Z"
  },
  "permissions": [
    "DEVICE_CONTROL",
    "EXECUTE",
    "NETWORK",
    "READ",
    "SENSITIVE_ACTION",
    "WRITE"
  ]
}
```

#### `POST /api/v1/auth/logout`
Revokes the server-side session in PostgreSQL, invalidates the cookie with `Max-Age=0`, and logs the `logout` audit event.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "message": "Successfully logged out"
}
```

#### `POST /api/v1/auth/cleanup-sessions`
Administrative maintenance endpoint requiring `SENSITIVE_ACTION` permission. Purges all expired sessions from the database.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "message": "Cleaned up 3 expired session(s)"
}
```

---

### 2. Comprehensive Health Check

`GET /api/v1/health`

Evaluates overall service operational state and checks all underlying dependencies.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "service": "jenna-api",
  "version": "0.2.0",
  "phase": "Phase 2 — Backend Core + Database",
  "timestamp": "2026-09-12T16:45:35.733541+00:00",
  "services": [
    {
      "name": "postgresql",
      "status": "healthy",
      "detail": null
    },
    {
      "name": "redis",
      "status": "healthy",
      "detail": null
    }
  ]
}
```

---

### 2. Liveness Probe

`GET /api/v1/health/live`

Process uptime check used by container orchestrators and load balancers to detect if the HTTP process is responsive.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "service": "jenna-api",
  "timestamp": "2026-09-12T16:45:35.773021+00:00"
}
```

---

### 3. Readiness Probe

`GET /api/v1/health/ready`

Readiness probe that actively validates connectivity to critical infrastructure (PostgreSQL, Redis). If any critical service is unavailable, the endpoint returns HTTP `503 Service Unavailable` with `ready: false`.

**Response `200 OK` (Healthy)**:
```json
{
  "status": "ok",
  "service": "jenna-api",
  "ready": true,
  "timestamp": "2026-09-12T16:45:35.809121+00:00",
  "dependencies": [
    {
      "name": "postgresql",
      "status": "healthy",
      "detail": null
    },
    {
      "name": "redis",
      "status": "healthy",
      "detail": null
    }
  ]
}
```

**Response `503 Service Unavailable` (Dependency Failure)**:
```json
{
  "status": "not_ready",
  "service": "jenna-api",
  "ready": false,
  "timestamp": "2026-09-12T16:45:35.809121+00:00",
  "dependencies": [
    {
      "name": "postgresql",
      "status": "unhealthy",
      "detail": "connection timeout"
    },
    {
      "name": "redis",
      "status": "healthy",
      "detail": null
    }
  ]
}
```

---

### 4. System Telemetry & Metadata

`GET /api/v1/system/info`

Returns runtime telemetry, uptime counter, environment, and observed dependencies.

**Response `200 OK`**:
```json
{
  "service": "jenna-api",
  "name": "Jenna AI",
  "version": "0.2.0",
  "phase": "Phase 2 — Backend Core + Database",
  "environment": "development",
  "status": "running",
  "timestamp": "2026-09-12T16:45:35.848923+00:00",
  "uptime_seconds": 37.2,
  "dependencies": {
    "postgresql": "healthy",
    "redis": "healthy"
  }
}
```

---

## WebSocket Protocol

### Connection Endpoint

`ws://localhost:8000/api/v1/ws`

**Query Parameters**:
- `client_id` *(optional, string)*: Client identifier. A UUID is generated if omitted.
- `token` *(optional, string)*: Authentication token hook (prepared for Phase 3).

### Initial Handshake Acknowledgement

Upon connecting, the server immediately emits a connection confirmation event:

```json
{
  "type": "connection_established",
  "client_id": "client-uuid",
  "timestamp": "2026-09-12T16:45:48.219653+00:00",
  "service": "jenna-api",
  "features": ["heartbeat", "events", "subscriptions"]
}
```

### Heartbeat (Ping / Pong)

Clients maintain heartbeat by sending `ping`:

**Client Request**:
```json
{
  "type": "ping"
}
```

**Server Response**:
```json
{
  "type": "pong",
  "timestamp": "2026-09-12T16:45:48.223715+00:00",
  "client_id": "client-uuid"
}
```

### Channel Subscription

Clients can subscribe to realtime event topics:

**Client Request**:
```json
{
  "type": "subscribe",
  "channels": ["system_health", "telemetry"]
}
```

**Server Response**:
```json
{
  "type": "subscribed",
  "channels": ["system_health", "telemetry"],
  "timestamp": "2026-09-12T16:45:48.226076+00:00"
}
```

### Future Extension Events

Prepared hooks acknowledge events with a graceful pending status:
- `ai_stream`
- `voice_event`
- `agent_event`
### 4. AI Core & Model Router Endpoints

#### `POST /api/v1/ai/generate`
Generates a complete (non-streaming) AI completion through the active provider, with automatic task routing, retry backoff, usage logging, and audit tracking.

**Request Body**:
```json
{
  "messages": [
    {"role": "system", "content": "You are Jenna, an autonomous personal assistant."},
    {"role": "user", "content": "Explain quantum computing in one sentence."}
  ],
  "task_type": "CHAT",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

**Response `200 OK`**:
```json
{
  "id": "gen_88f921d2-0657-4144-8840-02359ba9da85",
  "model": "gemini-2.5-flash",
  "provider": "gemini",
  "message": {
    "role": "assistant",
    "content": "Quantum computing leverages superposition and entanglement to solve complex computational problems exponentially faster than classical systems."
  },
  "usage": {
    "prompt_tokens": 24,
    "completion_tokens": 19,
    "total_tokens": 43
  },
  "latency_ms": 520.4,
  "finish_reason": "stop"
}
```

#### `POST /api/v1/ai/stream`
Generates a real-time Server-Sent Events (SSE) stream of token deltas for conversational UI responsiveness.

**Event Stream**:
- `stream.started`: Contains provider, model, and correlation metadata.
- `stream.delta`: Emits incremental token chunks as generated.
- `stream.completed`: Concludes generation with finish reason and usage metrics.
- `stream.error`: Emitted in case of provider failure, timeout, or rate limiting.

#### `GET /api/v1/ai/models`
Returns the list of currently configured and supported AI models across all active providers, including capabilities, context window, and recommended tasks.

#### `GET /api/v1/ai/status`
Returns real-time provider availability status (Google Gemini, OpenAI), active default model, and configured capabilities without exposing API keys.

#### `GET /api/v1/ai/usage`
Returns token consumption summaries, total requests, and recent usage history for the authenticated user.

---

### 5. Conversation & Multi-turn Reasoning Endpoints

#### `GET /api/v1/conversations`
Returns a paginated list of conversations belonging to the authenticated user, ordered by most recently updated.

#### `POST /api/v1/conversations`
Initializes a new conversation thread for the authenticated user.
```json
{
  "title": "New Conversation"
}
```

#### `GET /api/v1/conversations/{id}`
Returns details for a conversation, including recent messages in chronological order, with strict user isolation.

#### `PATCH /api/v1/conversations/{id}`
Renames an existing conversation owned by the authenticated user.
```json
{
  "title": "Renamed Conversation Title"
}
```

#### `DELETE /api/v1/conversations/{id}`
Deletes the conversation and cascades deletion of all associated messages.

#### `GET /api/v1/conversations/{id}/messages`
Fetches paginated messages from a specific conversation in chronological order.

#### `POST /api/v1/conversations/{id}/messages`
Submits a user message, runs the complete reasoning pipeline (Task Classification $\to$ Context Building $\to$ Model Routing $\to$ Response Validation $\to$ Persistence), and returns the assistant response.

#### `POST /api/v1/conversations/{id}/stream`
Submits a user message and streams assistant response tokens via Server-Sent Events (SSE), persisting the completed message in the database upon finish.

---

### 6. Settings & Persona Configuration Endpoints

#### `GET /api/v1/settings/personality`
Returns the active personality, tone, verbosity, and language preferences for the authenticated user.

#### `PUT /api/v1/settings/personality`
Updates personality settings for the authenticated user:
```json
{
  "assistant_name": "Jenna",
  "personality_style": "warm",
  "response_style": "conversational",
  "preferred_language": "auto",
  "preferred_locale": "en-IN",
  "verbosity": "normal",
  "formality": "casual",
  "humor_level": "subtle"
}
```

### 7. Memory & Cognitive Retrieval Endpoints

> **Privacy Mandate:** Memory is user-scoped and sensitive credentials are not stored.

#### `POST /api/v1/memory`
Creates a persistent memory with automatic semantic vector embedding generation (using `text-embedding-004` or `text-embedding-3-small`) and privacy gate validation.

#### `GET /api/v1/memory`
Paginated list of memories. Supports filtering by:
- `status`: `ACTIVE`, `ARCHIVED`, `SUPERSEDED`, `ALL` (default excludes `DELETED`)
- `memory_type`: `FACT`, `PREFERENCE`, `PERSONAL_CONTEXT`, `INSTRUCTION`, etc.
- `search`: Keyword search in content/summary
- `min_importance`: Minimum importance weight threshold [0.0 - 1.0]

#### `GET /api/v1/memory/{id}`
Fetch a single memory item by UUID (strict user ownership validation, 404 if deleted).

#### `PATCH /api/v1/memory/{id}`
Update memory content, importance, or metadata (re-computes vector embedding if content changed).

#### `DELETE /api/v1/memory/{id}`
Soft-deletes a memory record (sets `status = DELETED`). Excluded permanently from all future retrieval queries.

#### `POST /api/v1/memory/search`
Semantic vector similarity search using HNSW cosine index and compound relevance scoring ($0.5 \cdot S_{\text{sem}} + 0.2 \cdot S_{\text{imp}} + 0.2 \cdot S_{\text{rec}} + 0.1 \cdot S_{\text{conf}}$).

#### `POST /api/v1/memory/extract`
Extracts candidate memories from conversational text, performs sensitivity classification and deduplication comparison without persisting.

#### `POST /api/v1/memory/confirm`
User confirmation endpoint to persist or discard an extracted candidate memory.

#### `POST /api/v1/memory/{id}/archive`
Transitions memory lifecycle state to `ARCHIVED`.

#### `POST /api/v1/memory/{id}/restore`
Restores an archived or superseded memory back to `ACTIVE`.

#### `POST /api/v1/memory/{id}/feedback`
Applies user feedback (`USEFUL`, `INCORRECT`, `OUTDATED`, `FORGET`, `EDIT`) to safely update confidence, importance, or lifecycle state.

#### `GET /api/v1/memory/working`
List ephemeral short-term working memory items for the user.

#### `POST /api/v1/memory/working`
Store an ephemeral item in Redis working memory with TTL.

#### `DELETE /api/v1/memory/working`
Clear ephemeral short-term working memory items.

---

## Database Models & Schema

All models use UUID primary keys and standard timezone-aware timestamps (`created_at`, `updated_at`).

### 1. `users`
- `id` (UUID, Primary Key)
- `created_at` (Timestamp with timezone, NOT NULL)
- `updated_at` (Timestamp with timezone, NOT NULL)

### 2. `sessions`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id` ON DELETE CASCADE, NOT NULL, Indexed)
- `created_at` (Timestamp with timezone, NOT NULL)
- `expires_at` (Timestamp with timezone, NOT NULL, Indexed)

### 3. `audit_events`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id` ON DELETE SET NULL, Nullable, Indexed)
- `event_type` (VARCHAR(64), NOT NULL, Indexed)
- `action` (VARCHAR(128), NOT NULL)
- `success` (BOOLEAN, NOT NULL, Default True, Indexed)
- `request_id` (VARCHAR(64), Nullable, Indexed)
- `metadata` (JSONB on PostgreSQL, NOT NULL, Default `{}`)
- `created_at` (Timestamp with timezone, NOT NULL, Indexed)

### 4. `system_settings`
- `id` (UUID, Primary Key)
- `key` (VARCHAR(128), Unique, NOT NULL, Indexed)
- `value` (JSONB on PostgreSQL, NOT NULL)
- `created_at` (Timestamp with timezone, NOT NULL)
- `updated_at` (Timestamp with timezone, NOT NULL)

### 5. `ai_usage_logs`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id` ON DELETE SET NULL, Nullable, Indexed)
- `provider` (VARCHAR(64), NOT NULL, Indexed)
- `model` (VARCHAR(128), NOT NULL, Indexed)
- `prompt_tokens` (INTEGER, NOT NULL, Default 0)
- `completion_tokens` (INTEGER, NOT NULL, Default 0)
- `total_tokens` (INTEGER, NOT NULL, Default 0)
- `latency_ms` (FLOAT, NOT NULL)
- `status` (VARCHAR(32), NOT NULL, Default 'success', Indexed)
- `error_message` (TEXT, Nullable)
- `created_at` (Timestamp with timezone, NOT NULL, Indexed)

### 6. `conversations`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id` ON DELETE CASCADE, NOT NULL, Indexed)
- `title` (VARCHAR(255), NOT NULL, Default 'New Conversation')
- `created_at` (Timestamp with timezone, NOT NULL)
- `updated_at` (Timestamp with timezone, NOT NULL, Indexed)

### 7. `messages`
- `id` (UUID, Primary Key)
- `conversation_id` (UUID, Foreign Key -> `conversations.id` ON DELETE CASCADE, NOT NULL, Indexed)
- `role` (VARCHAR(32), NOT NULL) — 'user', 'assistant', 'system'
- `content` (TEXT, NOT NULL)
- `model` (VARCHAR(128), Nullable)
- `provider` (VARCHAR(64), Nullable)
- `metadata` (JSONB on PostgreSQL, NOT NULL, Default `{}`)
- `created_at` (Timestamp with timezone, NOT NULL, Indexed)

### 8. `memories`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id` ON DELETE CASCADE, NOT NULL, Indexed)
- `conversation_id` (UUID, Foreign Key -> `conversations.id` ON DELETE SET NULL, Nullable, Indexed)
- `superseded_by_id` (UUID, Foreign Key -> `memories.id` ON DELETE SET NULL, Nullable, Indexed)
- `status` (VARCHAR(32), NOT NULL, Default 'ACTIVE', Indexed) — 'CANDIDATE', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED', 'DELETED'
- `memory_type` (VARCHAR(32), NOT NULL, Indexed) — 'FACT', 'PREFERENCE', 'PERSONAL_CONTEXT', 'INSTRUCTION', 'CONVERSATION_SUMMARY', 'TASK_CONTEXT', 'TEMPORARY'
- `content` (TEXT, NOT NULL)
- `summary` (TEXT, Nullable)
- `importance` (FLOAT, NOT NULL, Default 0.5)
- `confidence` (FLOAT, NOT NULL, Default 0.8)
- `source` (VARCHAR(64), NOT NULL, Default 'MANUAL', Indexed) — 'USER_EXPLICIT', 'USER_CONVERSATION', 'SYSTEM', 'IMPORTED', 'MANUAL'
- `metadata` (JSONB on PostgreSQL, NOT NULL, Default `{}`)
- `embedding` (VECTOR(768), Nullable, Indexed with HNSW Cosine Index)
- `archived_at` (Timestamp with timezone, Nullable)
- `last_accessed_at` (Timestamp with timezone, NOT NULL, Indexed)
- `created_at` (Timestamp with timezone, NOT NULL, Indexed)
- `updated_at` (Timestamp with timezone, NOT NULL)

---

## Database Migration Commands

All database schema migrations are managed via Alembic:

```bash
# Create a new automatic migration revision
alembic revision --autogenerate -m "description_of_change"

# Upgrade database to latest revision
alembic upgrade head

# Downgrade database by one revision
alembic downgrade -1

# Downgrade database to base (empty)
alembic downgrade base

# Check current revision
alembic current

# View migration history
alembic history --verbose
```
