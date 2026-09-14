# Nexus AI — System Architecture

Nexus AI is engineered as an autonomous, modular desktop AI assistant built with strict separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                      NEXUS DESKTOP (Electron)               │
│  - Secure IPC                                              │
│  - Preload ContextBridge                                    │
│  - Native Windows OS Integration                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      FRONTEND LAYER (React/Vite)            │
│  - Cyber Command Center UI                                  │
│  - Live Agent Visualizer                                    │
│  - Human-in-the-Loop Security Modals                         │
│  - 9 Specialized Views (Chat, Agents, Tasks, Files, etc.)   │
└──────────────────────────┬──────────────────────────────────┘
            REST API (HTTP)│ ▲ WebSocket (Live Stream)
                           ▼ │
┌────────────────────────────┴────────────────────────────────┐
│                      BACKEND LAYER (FastAPI)                │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 NEXUS ORCHESTRATOR                    │  │
│  │   - Intent Classification                             │  │
│  │   - Multi-Step Workflow Planner                       │  │
│  │   - Telemetry & Synthesis                             │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ Delegations                      │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │                   9 SPECIALIZED AGENTS                │  │
│  │  Computer | File | Web | Code | Productivity          │  │
│  │  Comms | Data | Creative                              │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ Tool Invocations                 │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │                   MODULAR TOOLS                       │  │
│  │  Filesystem | Computer | Browser | Code | Calendar    │  │
│  │  Documents | System Commands                          │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ Auditing & Gates                 │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │            HUMAN-IN-THE-LOOP SECURITY ENGINE          │  │
│  │   - Risk Level Evaluation (Low / Medium / High)       │  │
│  │   - Pending Authorization Tickets                     │  │
│  │   - Persistent Audit Table                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  DATABASE (SQLite + SQLAlchemy): Chats, Tasks, Audits       │
└─────────────────────────────────────────────────────────────┘
```

## Architectural Isolation Guarantees
1. **Frontend Independence**: The frontend contains zero Python or server-side logic. Changing styling or components never requires modifying backend code.
2. **Backend Independence**: The backend runs as a standalone FastAPI service (`python -m uvicorn app.main:app --reload`).
3. **Agent Independence**: Each agent is contained within its own package (`backend/app/agents/<agent_name>/`). Adding or modifying an agent never requires changing other agents.
4. **Tool Isolation**: Tools are pure functions with typed schemas and risk levels.
5. **Zero-Key Demo Mode**: Operates out-of-the-box in local demo mode without needing paid API keys.
