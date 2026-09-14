# NEXUS AI — Intelligent Desktop Operating Layer

> **A production-ready, modular full-stack Windows desktop AI assistant.**

---

## 🌟 Architectural Overview

Nexus AI is engineered with strict separation of concerns across every layer:

```
Nexus-AI/
├── frontend/          # Independent React + TypeScript + Vite + Tailwind CSS application
├── backend/           # Independent FastAPI + Python service with modular agents and tools
│   ├── app/
│   │   ├── agents/    # 9 isolated agent packages + Orchestrator
│   │   ├── tools/     # 7 isolated tool domains (filesystem, computer, code, etc.)
│   │   ├── services/  # LLM (Multi-provider + Demo Mode), WebSockets, Security
│   │   └── api/       # REST and WebSocket endpoints
├── desktop/           # Independent Electron Windows desktop application with secure IPC
├── database/          # SQLite schema, migrations, seed scripts
├── shared/            # Shared TypeScript contracts, models, and constants
├── scripts/           # PowerShell and shell orchestration scripts
├── docs/              # In-depth architectural, API, and security documentation
├── package.json       # Root dev orchestration
└── README.md
```

Each subsystem can be opened, modified, and executed completely independently:
- Work **ONLY** on the UI: `cd frontend && npm run dev`
- Work **ONLY** on AI agents: `cd backend && python -m uvicorn app.main:app --reload`
- Work **ONLY** on Electron desktop: `cd desktop && npm start`

---

## 🤖 The 9 Autonomous Agents

| Agent | Responsibility | Key Tools |
| :--- | :--- | :--- |
| **Nexus Orchestrator** | Central intelligence, multi-step planning, delegation & synthesis | `planner`, `delegator`, `synthesizer` |
| **Computer Controller** | App launching, screen capture, window control, hardware vitals | `launch_app`, `capture_screenshot`, `get_system_info` |
| **Filesystem Operator** | File discovery, directory traversal, safe creation & deletion | `search_files`, `read_file`, `create_file`, `delete_file` |
| **Web Navigator** | Live search queries, webpage scraping, documentation retrieval | `search_web`, `fetch_webpage` |
| **Code Architect** | Syntax inspection, AST diagnostics, sandboxed execution | `analyze_code_structure`, `execute_code_sandbox` |
| **Productivity Executive** | Schedule blocking, agenda management, meeting brief formatting | `list_calendar_events`, `schedule_calendar_event` |
| **Comms Dispatcher** | Professional emails, Slack/announcement drafts, notifications | `draft_email`, `format_announcement` |
| **Data Scientist** | CSV/JSON analysis, aggregation statistics, chart shaping | `inspect_excel`, `calculate_metrics` |
| **Creative Studio** | Whitepaper drafting, UI copywriting, markdown publications | `create_docx_summary`, `format_document` |

---

## 🛡️ Human-in-the-Loop Security Gate

Dangerous actions (`delete_file`, `execute_command`, `kill_process`) are protected:
1. Agent attempts to perform a sensitive operation.
2. The engine halts execution and issues a security ticket (`sec-xxxxxxxx`).
3. The UI renders an interactive authorization prompt with `[Cancel]` and `[Allow]`.
4. Only upon explicit user confirmation does the operation proceed.

---

## 🚀 Quick Start

### 1. Automated Setup
Install dependencies across all subsystems in one command:
```powershell
# PowerShell
powershell -ExecutionPolicy Bypass -File scripts/setup/setup.ps1
```

### 2. Start Development Environment
Launch both Backend and Frontend concurrently:
```powershell
# PowerShell
powershell -ExecutionPolicy Bypass -File scripts/start-dev/start-dev.ps1
```
Or start independently:
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3 (Optional): Desktop Electron Shell
cd desktop
npm start
```

### 3. Open in Browser or Desktop
- **Web Command Center**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing

Run backend tests:
```bash
cd backend
python -m pytest
```

Verify frontend build:
```bash
cd frontend
npm run build
```

---

## 💡 Zero-Key Demo Mode

No API keys? No problem.
Nexus AI operates in full **Demo Mode** out of the box. All agents, planning pipelines, tools, and real-time WebSockets operate seamlessly with realistic simulations without requiring paid credentials. To use real cloud LLMs, simply add your `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` in the **Settings** tab.
