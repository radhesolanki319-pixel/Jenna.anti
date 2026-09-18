# Part 5 Implementation Handoff Guide — Jenna Personal AI
## Tools & Model Context Protocol (MCP) Integration

> **Status:** Part 1 (Foundation), Part 2 (AI Brain), Part 3 (Intelligent Memory), and Part 4 (Specialized Agents & Multi-Agent Orchestration) are 100% complete, verified, and locked.  
> **Next Architecture Milestone:** `PART 5 — TOOLS & MODEL CONTEXT PROTOCOL (MCP) INTEGRATION`.

---

## 1. Executive Summary

Jenna Personal AI possesses a multi-agent orchestration runtime, intelligent cognitive memory, and conversational AI brain:
- **Specialized Agent Registry**: 5 domain-tailored agents (`ResearchAgent`, `CodingAgent`, `AnalysisAgent`, `WritingAgent`, `GeneralTaskAgent`) with configurable step, token, and time budgets.
- **Task Planner & Decomposition**: Intent classification and bounded subtask planning (max 5 subtasks, max 15 steps) with safe structured context handoffs (zero internal chain-of-thought leakage).
- **Execution Telemetry & Safety**: PostgreSQL-backed task trees (`agent_tasks`) and granular per-step trace telemetry (`agent_step_traces`), with 3-tier authorization interactive confirmation challenges (`requires_confirmation`).
- **Interactive Control Center**: Next.js 14 Agent Control Center (`/agents`) providing interactive orchestration, live subtask inspection, and trace stream visualization.
- **Cognitive Memory & Brain**: Dual-tier Redis working memory + PostgreSQL `pgvector` semantic store, privacy filtering of sensitive credentials, multi-turn conversation engine with code-switching Hinglish persona.

Future tool implementations (Part 5) must interact with agents and execution loops through standardized interfaces, strictly adhering to user isolation and 3-tier authorization boundaries.

---

## 2. Directory Layout & Architecture Reference

```
jenna/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── ai/
│   │   │   │   ├── agents/             # Part 4 Agent Subsystem
│   │   │   │   │   ├── base.py         # BaseAgent & TaskStep abstractions
│   │   │   │   │   ├── planner.py      # TaskPlanner & AgentOrchestrator
│   │   │   │   │   ├── registry.py     # AgentRegistry
│   │   │   │   │   ├── runner.py       # Execution loop & cancellation tokens
│   │   │   │   │   ├── specialized.py  # 5 Specialized Agent implementations
│   │   │   │   │   └── types.py        # AgentTask, Budget, Handoff contracts
│   │   │   │   ├── memory/             # Cognitive Memory Subsystem
│   │   │   │   ├── providers/          # Gemini, OpenAI & Mock Providers
│   │   │   │   └── personality.py      # Female persona & Hinglish adaptation
│   │   │   ├── interfaces/             # ToolExecutor, AgentRunner, AIProvider contracts
│   │   │   ├── models/                 # AgentTask, AgentStepTrace, Memory, User, Session
│   │   │   ├── repositories/           # AgentTaskRepository, MemoryRepository, UserRepo
│   │   │   ├── routers/                # /api/v1/agents, /api/v1/memory, /api/v1/chat
│   │   │   ├── schemas/                # Pydantic validation schemas for tasks & traces
│   │   │   └── services/               # AgentRunnerService, MemoryService, AIService
│   │   ├── alembic/                    # Database migrations (a8b2c3d4e5f6 agent tasks)
│   │   └── tests/                      # 104 passing backend tests (100% pass rate)
│   └── web/                            # Next.js 14 Web Dashboard
│       ├── src/app/agents/page.tsx     # Agent Control Center (Orchestrator, Registry, Telemetry)
│       ├── src/app/memory/page.tsx     # Memory Control Center
│       ├── src/lib/api.ts              # Typed ApiClient with Agent API methods
│       └── tests/                      # 35 passing frontend tests (100% pass rate)
├── packages/
│   ├── shared/                         # Shared utility functions
│   └── types/                          # TypeScript types (AgentTask, Budget, Trace, Registry)
└── docs/                               # System Documentation
```

---

## 3. High-Level Agent & Tool Integration Blueprint

Specialized agents in `apps/api/app/ai/agents/` are designed to invoke tools registered in a centralized `ToolRegistry` adhering to the `ToolExecutor` interface (`app/interfaces/tool.py`).

### 3.1 Tool Calling Contract
Every tool must define:
1. **Name & Description**: Unique string identifier and human/LLM-readable description.
2. **Input Schema**: Typed Pydantic schema validating arguments before execution.
3. **Authorization Tier**:
   - `ALLOWED`: Safe, read-only tools (e.g. calculator, read-only file search, weather lookup).
   - `REQUIRES_CONFIRMATION`: Mutating or external actions (e.g. write file, run bash command, external network dispatch).
   - `DENIED`: Prohibited actions (e.g. accessing `/dev`, raw root filesystem manipulation).
4. **Execution Function**: Async callable executing within bounded timeouts.

### 3.2 Model Context Protocol (MCP) Client
Part 5 will introduce an MCP client adapter allowing Jenna to dynamically discover and execute tools exposed by external MCP servers (e.g., Brave Search MCP, GitHub MCP, SQLite MCP):
- Support stdio and SSE transport protocols.
- Map external MCP tool definitions into Jenna's native `Tool` registry.
- Enforce the 3-tier authorization challenge whenever an MCP tool is marked high-impact.

---

## 4. Immediate Next Steps for Part 5

1. **Concrete `ToolExecutor` Implementation**:
   - Create `apps/api/app/ai/tools/executor.py` implementing `app/interfaces/tool.py`.
   - Build `apps/api/app/ai/tools/registry.py` for dynamic tool lookup and capability exposure.

2. **Standard Builtin Tools**:
   - `calculator`: Safe deterministic mathematical evaluation.
   - `filesystem`: Scoped file reading, listing, and writing within configured project directory.
   - `web_search`: Factual search queries for `ResearchAgent`.
   - `terminal`: Bounded command execution with strict timeouts and whitelist/blacklist filters.

3. **Multi-Turn Tool Execution Loop in `AgentRunnerService`**:
   - Connect LLM tool-calling responses to the tool executor.
   - Inject tool outputs into subsequent agent reasoning steps.
   - Automatically transition tasks to `WAITING` status if a tool requires user confirmation.

4. **Web Tools & MCP Control Center**:
   - Upgrade `apps/web/src/app/tools/page.tsx` from placeholder into interactive tool manager.
   - Allow user to inspect installed tools, test tool execution, and configure MCP servers.
