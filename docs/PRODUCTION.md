# Production Deployment & Operations Guide — Jenna Personal AI

> **Status:** Production Ready (Part 11 Completed & Verified)  
> **Environment:** Native Linux / Termux (AArch64 / x86_64)

---

## 1. System Architecture Overview

The Jenna Personal AI platform is organized as a unified, high-performance monorepo running natively on Linux/Termux without reliance on emulation, Docker, or virtualization:

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend                       │
│     (App Router, Tailwind CSS, SSE Streaming, Port 3000)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / WebSocket (Credentials: Include)
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Core                      │
│     (Async Python 3.14+, Pydantic V2, Starlette, Port 8000)  │
├──────────────────────────────┬──────────────────────────────┤
│       AI Orchestrator        │        Security & Quotas     │
│  - Model Router (Gemini/OAI) │  - 3-Tier Action Gatekeeper  │
│  - Specialized Agent Fleet   │  - 60 RPM Sliding Window     │
│  - Memory Vector Subsystem   │  - 150k Daily Token Budget   │
│  - Multimodal Vision & Voice │  - Emergency Stop Switch     │
└──────────────┬───────────────┴──────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼──────────────┐
│       PostgreSQL 16         ││          Redis 7            │
│   (pgvector, HNSW Cosine)   ││ (Cache, Pub/Sub, Fast Rate) │
└─────────────────────────────┘└─────────────────────────────┘
```

---

## 2. Environment Configuration

Production configuration is strictly driven by environment variables loaded through `app.core.config.Settings`:

| Variable | Default / Recommended | Purpose |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Enables production hardening and secure cookie flags |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Asynchronous PostgreSQL connection URI |
| `REDIS_URL` | `redis://localhost:6379/0` | High-speed cache and rate limiting store |
| `SESSION_SECRET` | *32-char cryptographically random hex* | Signs user session cookies and pairing tokens |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed web dashboard origins |
| `DEFAULT_RATE_LIMIT_RPM` | `60` | Per-IP sliding-window requests per minute |
| `DAILY_TOKEN_QUOTA` | `150000` | Per-user blended model token consumption ceiling |

---

## 3. Native Service Management (Termux / Linux)

### PostgreSQL & Redis
```bash
# Start PostgreSQL daemon
pg_ctl -D $PREFIX/var/lib/postgresql start

# Start Redis server
redis-server --daemonize yes
```

### Backend Service (FastAPI)
```bash
cd apps/api
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Frontend Dashboard (Next.js)
```bash
cd apps/web
npm run build
npm start -- -p 3000
```

---

## 4. Quotas, Rate Limiting & Throttling

Jenna enforces defensive sliding-window rate limiting and token consumption tracking:
- **API Sliding Window:** Maximum 60 requests per minute per IP / session. Exceeding requests receive `HTTP 429 Too Many Requests`.
- **Daily Token Quota:** 150,000 tokens allocated daily per user across prompt and completion models. When quota reaches 80%, warnings are emitted to telemetry; at 100%, LLM inference requests are throttled with structured fallback instructions.

---

## 5. Health Monitoring & Observability

- **Liveness Probe:** `GET /health/live` — Returns HTTP 200 immediately if process is responsive.
- **Readiness Probe:** `GET /health/ready` — Verifies database connection pool and Redis ping.
- **Comprehensive Status:** `GET /api/v1/health` — Full subsystem audit with PostgreSQL, Redis, and disk diagnostics.
- **Security Audit:** `GET /api/v1/production/security-audit` — Real-time automated verification of platform security invariants.

---

## 6. Security Invariant Enforcement

1. **System & Security Rules Outrank User Instructions:** No prompt injection or adversarial tool request can override system safety constraints.
2. **Untrusted Context Framing:** All external web scraped content, OCR text, and user media are framed within `<untrusted_external_content>` sandbox tags.
3. **3-Tier Action Gatekeeper:**
   - Tier 1 (`READ`, `LOW_RISK_ACTION`): Autonomous execution.
   - Tier 2 (`SENSITIVE_ACTION`): Requires explicit user confirmation modal.
   - Tier 3 (`CRITICAL_ACTION`): Requires dual-confirmation or root admin signoff.
4. **Emergency Stop (Kill Switch):**
   - Instant freeze of all agent loops, accessibility commands, and computer control interfaces via `POST /api/v1/devices/emergency-stop/activate`.
