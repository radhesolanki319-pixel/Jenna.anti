# Jenna AI — Personal AI Platform

> **Status:** Part 1 Foundation Complete | Part 2 AI Brain Complete | Part 3 Memory Complete | Part 4 Specialized Agents Complete | Part 5 Tools & MCP Complete | **Part 12 GPT-6 Astra High-Density Cognitive Engine Complete**

Jenna is a modular personal AI platform designed to evolve from a rock-solid infrastructure foundation into an intelligent, multi-device, autonomous personal assistant equipped with the complete cognitive and operational capability matrix of **GPT-6 Astra**.

---

## Architecture Overview

```
jenna/
├── apps/
│   ├── web/               # Next.js 14 + TypeScript Control Center (:3000)
│   └── api/               # FastAPI + Python Async Backend (:8000)
├── packages/
│   ├── shared/            # Shared constants, formatters, and utilities
│   └── types/             # Shared TypeScript types & domain event envelopes
├── infra/
│   └── docker/            # Docker Compose multi-service configurations
├── docs/                  # System Architecture, Security, API, Handoff Specs
├── docker-compose.yml     # Complete stack orchestration (web, api, postgres, redis)
├── .env.example           # Environment template with production validation
└── README.md
```

## Tech Stack & Capabilities

| Layer | Technology | Status | Description |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS | **Production Ready** | Responsive control center, dark/light theme, live telemetry & health, auth session lifecycle, interactive multi-turn streaming AI Chat with conversation drawer, stop generation, retry, persona configuration modal, full-featured Memory Control Center UI, and Next.js Agent Control Center (`/agents`) with interactive orchestration, registry inspection, and real-time execution trace telemetry. |
| **Backend API** | FastAPI, Python 3.12+, Uvicorn | **Production Ready** | Layered architecture (`routers` -> `services` -> `repositories` -> `models`), async I/O throughout, structured error handling with correlation IDs. |
| **AI Brain Core & GPT-6 Astra** | Google Gemini, OpenAI, GPT-6 Astra Matrix | **Production Ready** | High-density cognitive scaffolding covering all 5 Astra domains: Autonomous Operations, 3D/CAD/Physics Simulation, Enterprise Software Engineering, Frontier Mathematics, and Structural Asset & Document Synthesis. |
| **Zero-Amnesia Context Engine** | State Checkpoint & Anti-Loop Watchdog | **Production Ready** | Continuous codebase symbol tracking, architectural decision preservation, and hash-based anti-loop watchdog preventing repetition and forgetting in extreme-context sessions. |
| **Conversation Engine** | Multi-turn reasoning, Task Classifier, Context Builder, Response Validator | **Production Ready** | Full reasoning pipeline, sliding message window, natural Hindi/Hinglish/English adaptation, configurable female persona (Jenna), strict user isolation. |
| **Memory Subsystem** | pgvector (HNSW Cosine), Redis + TTL, Embedding Providers | **Production Ready** | User-isolated persistent vector storage (`memories`), dual-provider embeddings (`text-embedding-004` & `text-embedding-3-small`), compound relevance scoring, ephemeral working memory, defensive prompt injection isolation, automatic extraction, privacy filters, deduplication, conflict supersession, and lifecycle management. |
| **Specialized Agents** | 10 Specialized Agents (including 5 Astra Specialists), Task Planner, Orchestrator | **Production Ready** | Core specialists (`Research`, `Coding`, `Analysis`, `Writing`, `GeneralTask`) + Astra specialists (`Spatial3DAgent`, `EnterpriseDevOpsAgent`, `DocumentSynthesisAgent`, `FrontierMathAgent`, `AutonomousSystemAgent`), dynamic task decomposition, and safe context handoffs. |
| **Tools & MCP Platform** | PlatformToolExecutor, MCPClient, Astra Validators | **Production Ready** | Builtin calculators, filesystem, telemetry, web research pipeline, Model Context Protocol (MCP), and Astra validators (`blender_validator`, `latex_validator`, `spreadsheet_validator`). |
| **Database** | PostgreSQL 18 (asyncpg, pgvector) | **Production Ready** | Fully reversible Alembic migrations, UUID keys, models: `users`, `sessions`, `audit_events`, `system_settings`, `ai_usage_logs`, `conversations`, `messages`, `memories`, `agent_tasks`, `agent_step_traces`. |

| **Cache & Bus** | Redis 7+ | **Production Ready** | Asynchronous client supporting caching, sliding-window rate limiting, pub/sub, and ephemeral working memory. |
| **WebSocket** | Starlette / FastAPI WebSockets | **Production Ready** | Real-time channel subscriptions, bidirectional heartbeat (ping/pong), real-time AI token streaming (`ai.generate`). |
| **Security** | PBKDF2-HMAC-SHA256, HttpOnly Cookies | **Production Ready** | Constant-time password verification (600,000 rounds), hashed DB session tokens, 3-tier authorization (`ALLOWED`, `DENIED`, `REQUIRES_CONFIRMATION`), recursive audit log sanitization, sensitive credential filtering. |
| **Future Contracts** | Domain Interfaces & Events | **Standardized** | 8 extensible interfaces (`AIProvider`, `MemoryProvider`, `AgentRunner`, `ToolExecutor`, `DeviceController`, `VisionProvider`, `VoiceProvider`, `TaskScheduler`) and 14 typed `DomainEvent` classes. |

---

## Completed Milestones

### Part 1 — Foundation
- [x] **Phase 1: Project Foundation**: Monorepo layout, Next.js dashboard shell, FastAPI backend, Docker Compose orchestration, PostgreSQL & Redis services.
- [x] **Phase 2: Backend Core + Database**: Layered service/repo architecture, SQLAlchemy async models, reversible Alembic migrations, readiness/liveness health probes, WebSocket baseline.
- [x] **Phase 3: Security + Authentication**: PBKDF2 password hashing, server-side session management with HttpOnly cookies, RBAC (`admin`, `user`, `readonly`), audit logging.
- [x] **Phase 4: Dashboard + Backend Integration**: Jenna AI Control Center UI, system health dashboard with live latency, authentication UI flows, active status monitoring.
- [x] **Phase 5: Foundation Finalization + Future Interfaces + QA**: 3-tier permission decision engine, recursive audit metadata sanitization, 8 domain interface contracts, 14 domain events, 100% test coverage, comprehensive handoff specs.

### Part 2 — AI Brain
- [x] **Phase 1: AI Core + Provider Layer + Model Router**: Real LLM provider integrations (Google Gemini & OpenAI), normalized error hierarchy, intelligent task-based routing, fallback recovery, exponential backoff retries, universal timeout enforcement, SSE & WebSocket streaming, persistent `ai_usage_logs` database tracking, interactive Chat UI with live model selection.
- [x] **Phase 2: Jenna Conversation Engine + Female Personality + Reasoning**: Multi-turn conversation engine with persistent `conversations` and `messages` tables, configurable female AI persona (Jenna), natural Hindi/Hinglish/English code-switching, modular system instruction architecture, context builder with window trimming, task classifier, response quality validation, stop generation, retry, and personality settings modal.

### Part 3 — Memory
- [x] **Phase 1: Memory Foundation + Semantic Retrieval**: Dual-tier memory architecture (short-term working memory with Redis/TTL + persistent long-term vector memory with pgvector HNSW cosine indexing), pluggable embedding providers (Gemini & OpenAI), compound multidimensional relevance scoring (similarity, importance, recency, confidence), user-isolated memory CRUD, MemoryContextProvider integration with defensive data framing, and interactive Memory Control Center UI.
- [x] **Phase 2: Intelligent Memory + Automatic Memory Management**: Automated candidate extraction engine (`MemoryExtractor`), sensitive credential privacy protection (`PrivacyFilter` - default DO NOT STORE passwords, tokens, keys), extraction policy & trivial chatter filtering (`MemoryPolicy`), semantic and attribute conflict deduplication (`MemoryDeduplicator`), lifecycle state management (`CANDIDATE`, `ACTIVE`, `SUPERSEDED`, `ARCHIVED`, `DELETED`), automated retention rules, natural-language memory commands, user feedback mechanism (`USEFUL`, `INCORRECT`, `OUTDATED`, `FORGET`, `EDIT`), and interactive Extraction & Safety Playground in Next.js.

### Part 4 — Specialized Agents & Multi-Agent Orchestration
- [x] **Phase 1: Agent Runtime Foundation**: Concrete `AgentRunner` execution loop with timeout enforcement, cancellation tokens, retries, and working/long-term memory context injection. 5 domain-tailored agents (`ResearchAgent`, `CodingAgent`, `AnalysisAgent`, `WritingAgent`, `GeneralTaskAgent`) with default budgets and capability tags. Central `AgentRegistry`. Reversible Alembic migrations for `agent_tasks` and `agent_step_traces`.
- [x] **Phase 2: Multi-Agent Orchestration**: `TaskPlanner` with intent classification and bounded decomposition (max 5 subtasks, max 15 steps per agent). `AgentOrchestrator` coordinating sequential subtask execution trees with structured context handoffs (zero internal chain-of-thought leakage). 3-tier authorization interactive confirmation challenges (`requires_confirmation` / `WAITING` state). Next.js Agent Control Center (`/agents`) with interactive orchestration, registry inspection, and real-time execution trace telemetry.

### Part 5 — Tools & Model Context Protocol (MCP) Integration
- [x] **Phase 1: Tool Registry + MCP Foundation**: Concrete `PlatformToolExecutor` implementing `ToolExecutor` domain contract with schema validation, per-user 3-tier authorization (`ALLOWED`, `DENIED`, `REQUIRES_CONFIRMATION`), bounded timeouts, cancellation tokens, and output truncation safeguards. Standard builtin tools (`calculator` via AST node visitor, directory-scoped `filesystem_read`/`write` with path traversal defenses, `system_info` telemetry). Model Context Protocol (MCP) client abstraction supporting JSON-RPC 2.0 (`2024-11-05`), mock transport, dynamic tool discovery (`tools/list`), and execution (`tools/call`).
- [x] **Phase 2: Web Research + Real Approved Tools**: 6-stage Web Research Pipeline (`search` ➔ `collect` ➔ `open/read` ➔ `compare` ➔ `synthesize` ➔ `cite`) with source deduplication, HTML extraction without scripts/styles, regex prompt-injection neutralization, and strictly numbered source citations (`[1]`, `[2]`). Full Next.js Tool Manager (`/tools`) with Tool Catalog, interactive Playground, Web Research Studio, and MCP Server Manager. Deterministic test suites passing 100% (13 backend tests in `test_tools.py` and 6 frontend tests in `tools.test.mjs`).

---

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose (or local Node.js 20+ and Python 3.12+)
- PostgreSQL & Redis

### 2. Running with Docker Compose (Recommended)
```bash
cp .env.example .env
docker compose up -d
```
- Web Dashboard: [http://localhost:3000](http://localhost:3000)
- API Documentation: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 3. Running Locally for Development
```bash
# Start Backend
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Start Frontend
cd apps/web
npm install
npm run dev
```

---

## Verification & Testing

```bash
# Backend Test Suite (Pytest async)
cd apps/api
pytest -v

# Frontend Test Suite (Jest / Node Test Runner)
cd apps/web
npm test

# TypeScript Typecheck
cd apps/web
npm run typecheck
```

---

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API & WebSocket Specification](docs/API.md)
- [Security Architecture & Audit Policy](docs/SECURITY.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Project Roadmap](docs/ROADMAP.md)
- [Memory Architecture & Safety](docs/MEMORY.md)
- [Part 2 Implementation Handoff](docs/PART_2_HANDOFF.md)
- [Part 4 Implementation Handoff](docs/PART_4_HANDOFF.md)
- [Part 5 Implementation Handoff (Tools & MCP)](docs/PART_5_HANDOFF.md)
- [Part 6 Implementation Handoff (Voice & Vision)](docs/PART_6_HANDOFF.md)

---

## License

Private — All rights reserved.
