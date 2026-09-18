# Development Guide — Jenna AI Platform

> **Status:** Part 1 Foundation Complete | Environment: Linux / Docker / Termux

---

## 1. Prerequisites

- **Node.js**: 20+ (Node 22 LTS recommended)
- **Python**: 3.12+ (Python 3.12 / 3.14)
- **PostgreSQL**: 16+ (with `asyncpg` support)
- **Redis**: 7+
- **Docker & Docker Compose**: (for containerized deployments)

---

## 2. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Ensure production secrets have high entropy (minimum 16 characters) if `APP_ENV=production`.

### 2.1 AI Provider Configuration
Configure at least one real AI provider key:
```env
AI_PROVIDER=gemini        # 'gemini' | 'openai'
AI_MODEL=gemini-2.5-flash # or 'gpt-4o'
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
AI_REQUEST_TIMEOUT_SECONDS=30
AI_MAX_RETRIES=3
```

---

## 3. Local Development

### 3.1 Backend (FastAPI)

```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API server with live reload
uvicorn app.main:app --reload --port 8000
```
- API Documentation: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- AI Status: [http://localhost:8000/api/v1/ai/status](http://localhost:8000/api/v1/ai/status)

### 3.2 Frontend (Next.js 14)

```bash
cd apps/web
npm install
npm run dev
```
- Web Dashboard: [http://localhost:3000](http://localhost:3000)
- AI Chat Interface: [http://localhost:3000/chat](http://localhost:3000/chat)

### 3.3 Docker Compose (Full Stack)

```bash
docker compose up -d
docker compose ps
docker compose logs -f
```

---

## 4. Quality Gate & Testing

### 4.1 Backend Pytest Suite
Runs 70 comprehensive async test cases covering AI Core, provider routing, fallback, retries, SSE streaming, usage tracking, multi-turn conversation engine, personality settings, task classification, response validation, authentication, PBKDF2 hashing, cookie sessions, RBAC permissions, audit sanitization, 3-tier authorization, and WebSocket streaming:

```bash
cd apps/api
pytest -v
```

### 4.2 Frontend Unit Tests
Runs the Jest / Node test runner suite validating the API client, auth route guards, health aggregations, WebSocket backoff logic, and Chat UI multi-turn streaming logic (23 tests):

```bash
cd apps/web
npm test
```

### 4.3 TypeScript Typechecking
Validates all types across frontend pages, components, and `@jenna/types`:

```bash
cd apps/web
npm run typecheck
```

### 4.4 Database Migration Verification
Validate reversible migrations through a full downgrade/upgrade cycle:

```bash
cd apps/api
alembic downgrade base
alembic upgrade head
alembic downgrade -1
alembic upgrade head
alembic current
```

---

## 5. Architecture & Code Guidelines

1. **Thin Route Handlers**: Routers in `apps/api/app/routers/` perform schema validation and dispatch to services. No business logic belongs in route handlers.
2. **Repository Pattern**: All database interactions use repositories inheriting from `BaseRepository` in `apps/api/app/repositories/`.
3. **Audit Trail**: Every authorization failure, authentication lifecycle change, and high-risk action logs to `AuditEventRepository`. Metadata is automatically scrubbed by `sanitize_audit_metadata()`.
4. **3-Tier Permission Evaluation**: Sensitive actions check `PermissionService.evaluate_action(..., is_sensitive=True)` to produce `REQUIRES_CONFIRMATION` until interactively confirmed.
5. **Shared Types**: Add cross-stack interfaces to `packages/types/index.ts` so frontend and backend remain strictly synchronized.
