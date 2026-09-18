# 🌌 Google Antigravity -> Jenna: Master Architectural Integration Specification

> **Status:** SAVED & READY FOR INJECTION  
> **Target:** Jenna Personal AI Platform (`Antigravity-project/jenna`)  
> **Trigger Command:** *"yeh sab jenna ke ander daalna"* (or *"Antigravity features integrate karo"*)  
> **Version:** 3.0-Production Spec

---

## 📑 Table of Contents
1. [Executive Overview](#1-executive-overview)
2. [Complete Antigravity Feature Inventory](#2-complete-antigravity-feature-inventory)
   - 2.1 Autonomous Agentic Core (The Loop)
   - 2.2 Multi-Agent Swarm & Subagent System
   - 2.3 Code Navigation & Multi-File Patching Engine
   - 2.4 Terminal, Sandbox & Background Daemon Manager
   - 2.5 Reactive Scheduling & Autonomous Cron Engine
   - 2.6 Customization Ecosystem (Skills, Rules, Plugins, Hooks, Sidecars)
   - 2.7 Model Context Protocol (MCP) Integration
   - 2.8 Web Intelligence & Browser Automation
   - 2.9 Brain, Artifacts & Visual Generation Engine
   - 2.10 Interactive Decision Modal Engine
   - 2.11 Slash Commands Suite
3. [Jenna Architecture Mapping & Implementation Blueprint](#3-jenna-architecture-mapping)
4. [Activation Protocol](#4-activation-protocol)

---

## 1. Executive Overview
This specification details every single feature, engine, tool, protocol, and design pattern of **Google Antigravity (Advanced Agentic Coding by Google DeepMind)**. 
When activated, this entire suite will be native to **Jenna**, transforming her from a companion app with bash triggers into a self-contained, enterprise-grade Autonomous Agentic OS living inside Android/Termux.

---

## 2. Complete Antigravity Feature Inventory

### 2.1 Autonomous Agentic Core (The ReAct Loop)
* **Continuous Multi-Turn Autonomous Loop:** Unlike standard request-response chatbots, the agent enters an autonomous reasoning loop (`Think -> Select Tool -> Execute -> Observe Tool Result -> Re-evaluate`). It does not stop or request confirmation on trivial steps until the ultimate goal is 100% completed.
* **Context Budgeting & Auto-Compaction:** Dynamically measures token limits, archives completed trajectory chunks, and generates structured `CONTEXT_SUMMARY` checkpoints without losing variables, state, or user intent.
* **Error Self-Correction & Reflection:** Catches shell exit codes, Python exceptions, syntax errors, and lint IDs, automatically writing fixes and retrying.

### 2.2 Multi-Agent Swarm & Subagent System
* **Concurrent Subagent Dispatching (`invoke_subagent`):** Spawns independent subagents (`inherit`, `flash`, `flash_lite`, `pro` models) that run concurrently in separate background conversation threads without blocking the primary user chat.
* **Dynamic Agent Specialization (`define_subagent`):** Dynamically generates new subagent types at runtime with custom system prompts, scoped tools (read-only, write-enabled, MCP-enabled), and specific role objectives.
* **Workspace Isolation Modes:**
  - `inherit`: shares parent workspace.
  - `branch`: creates an isolated git/file workspace branch.
  - `share`: hardlinks repository directory for zero-duplicate storage.
* **Inter-Agent Messaging (`send_message` / `manage_subagents`):** Real-time pub/sub bus where parent agents monitor status, send mid-execution steering instructions, or terminate subagent trees.

### 2.3 Code Navigation & Multi-File Patching Engine
* **Precision Chunk Replacement (`replace_file_content`):** Modifies single or contiguous code chunks using exact string matching, line ranges (`StartLine`, `EndLine`), and lint error association—preventing file destruction from LLM hallucinations.
* **Safe Atomic File Creator (`write_to_file`):** Safely creates files, makes parent directories recursively, and enforces explicit overwrite protections.
* **Streaming File Inspector (`view_file`):** Handles text and binary files (PDFs, images, audio, video) with sliced windowing (up to 800 lines) and byte offset pagination (`ContentOffset`).
* **High-Speed Ripgrep Matcher (`grep_search`):** Regex-based code search across the entire project with include/exclude globs, line numbers, and content snippets.
* **Fd Discovery Engine (`find_by_name`):** Rapid file and directory tree indexing with glob matching and depth control.

### 2.4 Terminal, Sandbox & Background Daemon Manager
* **Synchronous & Asynchronous Execution (`run_command`):** Runs shell commands with a configurable `WaitMsBeforeAsync` threshold. Fast commands return instantly; long-running processes cleanly transition to background tasks without hanging.
* **Persistent Shell Terminals (`RequestedTerminalID`):** Preserves shell environment variables, virtualenvs, and exported flags across separate bash executions.
* **Background Task Controller (`manage_task`):**
  - Real-time log streaming (`.system_generated/tasks/task-<id>.log`).
  - Interactive STDIN pipe injection (`send_input`).
  - Process lifecycle management (`list`, `status`, `kill`).
* **Execution Sandbox & Permission Guardrails:** Configurable safety policies (`always-proceed`, `request-review`, `strict`, `proceed-in-sandbox`).

### 2.5 Reactive Scheduling & Autonomous Cron Engine
* **One-Shot Timers (`schedule`):** Non-blocking delayed executions with smart early termination conditions:
  - `never`: unconditional timer.
  - `any`: wakes up early if any subagent or background task reports an update.
  - `<sender-id>`: wakes up early if a specific process finishes.
* **Recurring Background Cron:** Standard 5-field cron syntax (`minute hour day month day-of-week`) with optional `MaxIterations` for automated health checks, background git syncs, and telemetry.
* **Zero-CPU Reactive Wakeup:** Agent process suspends cleanly without busy-waiting `while true` sleep loops, waking only when kernel signals or scheduler messages arrive.

### 2.6 Customization Ecosystem (Skills, Rules, Plugins, Hooks, Sidecars)
* **Skills System (`SKILL.md`):** Modular on-demand capabilities with YAML frontmatter, markdown instructions, reference docs, and executable scripts. Uses **Progressive Disclosure** (only names/descriptions loaded until triggered).
* **Hierarchical Rules Engine (`GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md`):** Folder-level guidelines that automatically load as the agent navigates directories.
* **Lifecycle Event Hooks (`hooks.json`):** Pre-tool and post-tool interceptors that validate actions, block dangerous commands, or format output before LLM consumption.
* **Plugin Bundles (`plugin.json`):** Packages skills, rules, and MCP configs into shareable units.
* **Sidecar Daemons:** Co-located services running alongside the agent.

### 2.7 Model Context Protocol (MCP) Integration
* **Standard JSON-RPC 2.0 Client (`mcp_config.json`):** Seamless connection to external tool servers (GitHub, PostgreSQL, Filesystems, Puppeteer/Playwright, Figma, Google Drive).
* **Dynamic Tool Discovery:** Discovers and registers tools on boot via stdio or SSE transports.

### 2.8 Web Intelligence & Browser Automation
* **Clean Markdown Scraper (`read_url_content`):** Fast HTTP fetcher that converts live HTML pages into clean Markdown, stripping CSS, scripts, and trackers without JavaScript overhead.
* **Domain-Biased Web Search (`search_web`):** Real-time web index queries with domain prioritization.
* **Browser Automation (`/browser`):** Headless Chromium integration for JavaScript-heavy single-page apps, clicking buttons, filling forms, and taking page screenshots.

### 2.9 Brain, Artifacts & Visual Generation Engine
* **Interactive Artifacts (`<appDataDir>/brain/<id>/`):** Specialized standalone markdown documents for architectural reports, interactive diffs, and persistent experiment tracking.
* **Mermaid Diagram Engine:** Generates flowcharts, sequence diagrams, state diagrams, class diagrams, ERDs, and XY charts.
* **Interactive Carousels:** Step-by-step UI progression sliders and before/after code walkthroughs.
* **AI Image & UI Generator (`generate_image`):** Native generation of UI mockups, icons, and diagrams with custom aspect ratios.

### 2.10 Interactive Decision Modal Engine
* **Modal Questions (`ask_question`):** Renders structured UI modals with single-select, multi-select checkboxes, and write-in fallbacks to clarify requirements or architectural decisions without raw text confusion.

### 2.11 Slash Commands Suite
* `/goal`: Overnight autonomous task runner that persists until goal criteria are met.
* `/plan`: Step-by-step interactive blueprinting.
* `/grill-me`: Deep architecture interview to stress-test decisions.
* `/browser`: Web browsing and scraper runner.
* `/schedule`: Timer and cron job scheduler.
* `/teamwork-preview`: Multi-agent team simulation.
* `/learn`: Pattern detection and permanent workflow rule memory.
* `/boost`: Rigorous multi-perspective verification and high-reasoning loop.

---

## 3. Jenna Architecture Mapping
When integrated, the components map directly into the existing repository:

| Antigravity Engine | Jenna Subsystem | Location in Project |
| :--- | :--- | :--- |
| **Agentic Loop** | Conversational Orchestrator | `apps/api/app/services/antigravity_agent.py` |
| **Subagent Swarm** | Background Worker Pool | `apps/api/app/ai/agents/runner.py` |
| **Skills & Rules** | Extensibility Engine | `apps/api/app/services/skills_service.py` |
| **Terminal & Sandbox** | Termux Bridge | `apps/api/app/services/termux_service.py` |
| **Background Tasks** | Async Task Daemon | `apps/api/app/services/task_manager.py` |
| **Scheduler / Cron** | Reactive Event Bus | `apps/api/app/services/scheduler_service.py` |
| **MCP Client** | Tool Gateway | `apps/api/app/ai/tools/mcp_client.py` |
| **Web & Browser** | Research Tools | `apps/api/app/ai/tools/web/` |
| **Artifacts & Brain** | Knowledge Store | `apps/api/app/services/artifact_service.py` |
| **Web UI Dashboard** | Next.js Frontend | `apps/web/src/components/` & `pages/` |
| **Screen Pet Sync** | Dexter Native Companion | `scripts/dexter_screen_pet.py` |

---

## 4. Activation Protocol
To trigger the automated integration, the user simply issues the command:
> **"yeh sab jenna ke ander daalna"** (or *"Antigravity features inject karo"*)

Upon receiving this trigger, the agent will systematically implement each engine module by module with full unit testing, database migrations, and web dashboard panels.
