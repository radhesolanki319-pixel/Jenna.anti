# Part 6 Implementation Handoff Guide — Jenna Personal AI
## Voice & Vision Subsystems

> **Status:** Part 1 (Foundation), Part 2 (AI Brain), Part 3 (Intelligent Memory), Part 4 (Specialized Agents), and Part 5 (Tools & MCP) are 100% complete, verified, and locked.  
> **Next Architecture Milestone:** `PART 6 — VOICE & VISION SUBSYSTEMS`.

---

## 1. Executive Summary

Jenna Personal AI possesses a multi-agent orchestration runtime, Model Context Protocol (MCP) tool execution engine, cognitive memory, and conversational AI brain:
- **Tools & MCP Execution**: `PlatformToolExecutor` enforcing 3-tier authorization (`ALLOWED`, `DENIED`, `REQUIRES_CONFIRMATION`), bounded timeouts, cancellation tokens, output truncation, and `<tool_output>` prompt containment.
- **Standard Builtin Platform Tools**: Safe AST calculator, directory-scoped filesystem tools with path traversal defenses, system telemetry, and a 6-stage Web Research pipeline (`search` ➔ `collect` ➔ `read` ➔ `compare` ➔ `synthesize` ➔ `cite`).
- **MCP Client**: Official JSON-RPC 2.0 protocol (`2024-11-05`) abstraction supporting stdio, SSE, and mock transports for dynamic remote tool discovery and invocation.
- **Specialized Agents**: 5 domain-tailored agents (`ResearchAgent`, `CodingAgent`, `AnalysisAgent`, `WritingAgent`, `GeneralTaskAgent`) with bounded task decomposition and safe handoffs.
- **Interactive Web Control Center**: Next.js 14 control centers for Chat (`/chat`), Memory (`/memory`), Agents (`/agents`), and Tools & MCP (`/tools`).

Future perception and multimodal implementations (Part 6) must build on these foundations while strictly respecting user privacy and explicit authorization boundaries.

---

## 2. Directory Layout & Architecture Reference

```
jenna/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── ai/
│   │   │   │   ├── tools/              # Part 5 Tools, MCP, & Web Research Subsystem
│   │   │   │   │   ├── builtin/        # calculator, filesystem, system
│   │   │   │   │   ├── mcp/            # protocol.py, client.py (JSON-RPC 2.0)
│   │   │   │   │   ├── web/            # provider.py, fetcher.py, researcher.py
│   │   │   │   │   ├── executor.py     # PlatformToolExecutor (3-tier auth & containment)
│   │   │   │   │   ├── registry.py     # Central ToolRegistry
│   │   │   │   │   └── types.py        # ToolDefinition, Result, Citation schemas
│   │   │   │   ├── agents/             # Part 4 Multi-Agent Subsystem
│   │   │   │   ├── memory/             # Part 3 Cognitive Memory Subsystem
│   │   │   │   ├── providers/          # Part 2 LLM Provider Layer
│   │   │   │   └── personality.py      # Female persona & Hinglish adaptation
│   │   │   ├── interfaces/             # VoiceProvider, VisionProvider, ToolExecutor contracts
│   │   │   ├── routers/                # /api/v1/tools, /api/v1/agents, /api/v1/memory, /api/v1/chat
│   │   │   └── services/               # ToolExecutor, AgentRunnerService, MemoryService
│   │   └── tests/                      # 117 passing backend tests (100% pass rate)
│   └── web/                            # Next.js 14 Web Dashboard
│       ├── src/app/tools/page.tsx      # Part 5 Tool Manager, Playground, Research, & MCP
│       ├── src/app/agents/page.tsx     # Part 4 Agent Control Center
│       ├── src/app/memory/page.tsx     # Part 3 Memory Control Center
│       └── tests/                      # 41 passing frontend tests (100% pass rate)
├── packages/
│   └── types/                          # Synchronized TypeScript declarations
└── docs/                               # System Documentation
```

---

## 3. Specifications for Part 6: Voice & Vision

### 3.1 Phase 1: Voice (Speech-to-Text & Text-to-Speech)
- **Abstract Contracts**: Implement `VoiceProvider` interface (`app/interfaces/voice.py`) with provider-agnostic abstractions for STT (audio -> text) and TTS (text -> audio stream).
- **Audio Transport & Privacy**:
  - Explicit microphone permission prompt; clear visual recording indicator (`is_recording`, `is_speaking`).
  - No silent microphone activation.
  - Do NOT store raw audio files on disk by default to preserve user privacy; store transcribed text only in standard conversation turns.
- **Jenna Female Persona & Accent**:
  - Natural female voice model profile configured in `system_settings`.
  - Seamless adaptation for English, Hindi (Devanagari), and romanized Hinglish phrases.
- **Interruption & Turn Detection**:
  - Streaming audio playback cancellation upon user barge-in / new speech detection.

### 3.2 Phase 2: Vision (Multimodal Understanding & Media Safety)
- **Abstract Contracts**: Implement `VisionProvider` interface (`app/interfaces/vision.py`) with support for image analysis, OCR, and diagram reasoning.
- **Multimodal Router Integration**:
  - Route image-attached requests to vision-capable models (e.g. `gemini-2.0-flash` or `gpt-4o`).
- **Untrusted Context Framing**:
  - Text extracted from OCR, diagrams, or user screenshots is treated as UNTRUSTED external input and cannot override system instructions or security policies.
- **Explicit Camera Permission**:
  - Never silently activate device camera; require user interaction and display active viewfinder.

---

## 4. Test & Quality Gate Checklist for Part 6
- [ ] Provider-agnostic mock voice provider for deterministic unit testing without external audio devices.
- [ ] Permission denial tests verifying microphone/camera requests fail gracefully when blocked.
- [ ] Image format validation (PNG, JPEG, WebP) and file size bounds (max 10MB).
- [ ] Zero raw audio leakage to database or persistent storage.
- [ ] Full backend tests (`pytest apps/api/tests`) and frontend tests (`npm test` in `apps/web`) passing with 100% success rate.
