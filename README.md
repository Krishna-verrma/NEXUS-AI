# NEXUS AI

> *"Turn complex problems into intelligent workflows."*

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg)](https://microsoft.com/windows)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Vite%20%7C%20Tailwind-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.14-009688.svg)](https://fastapi.tiangolo.com/)
[![Desktop](https://img.shields.io/badge/Desktop-Electron%2031-47848F.svg)](https://www.electronjs.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20(WAL%20Mode)-003B57.svg)](https://www.sqlite.org/)
[![Status](https://img.shields.io/badge/Tests-22%2F22%20Passing-brightgreen.svg)]()

**NEXUS AI** is an advanced desktop AI command center engineered for autonomous problem-solving. Instead of acting as a simple conversational chatbot, Nexus AI functions as a multi-agent workspace where high-level user tasks are dynamically decomposed, delegated to specialized agents, audited by a strict QA Reviewer, and synthesized into strategic executive deliverables.

---

## 🌟 Architecture & Workflow

```
                          ┌───────────────────────────┐
                          │       USER REQUEST        │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │    NEXUS ORCHESTRATOR     │
                          │ Dynamic Planning & DAG    │
                          └─────────────┬─────────────┘
                                        │
        ┌───────────────────────────────┼──────────────────────────────┐
        │                               │                              │
        ▼                               ▼                              ▼
┌──────────────┐                ┌──────────────┐               ┌──────────────┐
│ DATA ANALYST │                │RESEARCH AGENT│               │ CODING AGENT │
│ CSV/XLSX/JSON│                │Market Trends │               │ Polyglot Fix │
└───────┬──────┘                └───────┬──────┘               └───────┬──────┘
        │                               │                              │
        └───────────────────────────────┼──────────────────────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │        RISK AGENT         │
                          │ Multi-Dimensional Surface │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │      REVIEWER AGENT       │
                          │   Quality Assurance Gate  │
                          └──────┬─────────────▲──────┘
                                 │             │
                    Approved: Yes│             │ Approved: No (Max 2 retries)
                                 │             └─────── Revision Loop
                                 ▼
                          ┌───────────────────────────┐
                          │       REPORT AGENT        │
                          │ Executive Synthesis & MD  │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │       FINAL RESULT        │
                          │ Strategic Solution & Chat │
                          └───────────────────────────┘
```

---

## 🚀 Key Features

### 1. Dynamic Nexus Orchestrator (`backend/app/agents/orchestrator.py`)
- **Dynamic Task Planning**: Analyzes complexity and constructs a tailored agent Directed Acyclic Graph (DAG). Never hardcodes a fixed pipeline.
- **Context Passing**: Automatically cascades intermediate tabular data, market context, and risk matrices between agents.
- **Reviewer Quality Gate**: Integrates a feedback loop where outputs that fail consistency or completeness checks are revised up to 2 times.
- **Clean High-Level Telemetry**: Emits high-level status transitions without exposing private chain-of-thought dumps.

### 2. Specialized Multi-Agent Registry
1. 🧠 **Nexus Orchestrator**: Central planner and execution coordinator.
2. 📊 **Data Analyst Agent**: Real descriptive statistics (mean, median, std, min, max), anomaly detection, trend regression, and chart data generation for CSV/XLSX/JSON.
3. 🔎 **Research Agent**: Investigates industry trends, cites authoritative sources, and separates verified facts from strategic assumptions.
4. 💻 **Coding Agent**: Polyglot generation and debugging (C++, Python, Java, JS, TS, SQL) with safe review principles (no arbitrary auto-execution).
5. 📄 **Document Agent**: Deep structural extraction and Q&A on PDF, DOCX, and text briefs.
6. ⚠ **Risk Agent**: Maps business, technical, operational, cybersecurity, and data compliance risks with severity, probability, and actionable mitigations.
7. 🧐 **Reviewer Agent**: Validates accuracy, completeness, and consistency before approving results.
8. 📑 **Report Agent**: Synthesizes formal executive briefings with Executive Summary, Methodology, Key Findings, In-Depth Analysis, Risk Matrices, and Actionable Recommendations.

### 3. Glassmorphic AI Command Center UI
- Custom dark-theme desktop interface built with React 18, TypeScript, and Tailwind CSS.
- Real-time agent status cards with live state transitions, animated pulses, duration clocks, and output inspection modals.
- Interactive workflow visualizer (Cards and Pipeline views).
- Grounded follow-up chat drawer to continue querying the completed task context.
- Full markdown & HTML report exporter.

### 4. Deterministic Hackathon Demo Mode
- **Zero Configuration**: Works out-of-the-box without an API key or internet connection.
- **Authentic Sales Dataset**: Processes `data/demo_sales.csv` with real tabular calculation of revenue contraction and customer retention decay.
- **Reliable Execution**: 100% deterministic, passing all quality checks and generating complete strategic deliverables.

### 5. Cybersecurity & Safe Desktop Sandbox
- **Electron Security**: `contextIsolation: true`, `nodeIntegration: false`, secure IPC preload bridge.
- **Upload Hardening**: Path traversal prevention, extension allowlisting, and 25MB file limits.
- **Credential Protection**: API keys are masked and persisted strictly in local SQLite (`nexus_ai.db`).

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Desktop** | Electron 31, Electron Builder (NSIS & Portable targets) |
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS, Lucide Icons |
| **Backend** | Python 3.14, FastAPI, Uvicorn, Pydantic v2 |
| **Database** | SQLite 3 with WAL mode and foreign key constraints |
| **Real-Time** | WebSockets (`ws://127.0.0.1:8000/ws/tasks/{id}`) |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |

---

## 📂 Project Structure

```
nexus-ai/
├── frontend/                     # React + TypeScript + Vite UI
│   ├── src/
│   │   ├── components/           # UI, Layout, Workspace, Chat, Reports
│   │   ├── pages/                # Dashboard, Workspace, Agents, Files, History, Reports, Settings
│   │   ├── hooks/                # useWebSocket, useTasks
│   │   ├── services/             # REST & WebSocket API clients
│   │   ├── types/                # TypeScript domain models
│   │   └── utils/                # Formatters, Electron bridge
│   └── package.json
│
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── agents/               # Orchestrator & 7 specialized agents
│   │   ├── api/                  # REST endpoints & WebSocket handler
│   │   ├── core/                 # Config, AI client, Security, Event bus
│   │   ├── database/             # SQLite connection & CRUD repository
│   │   ├── models/               # Pydantic schema models
│   │   ├── services/             # Task, File, Chat, and Demo services
│   │   └── main.py               # Application entrypoint
│   ├── requirements.txt
│   └── .env.example
│
├── desktop/                      # Electron application
│   ├── main/index.js             # Window supervisor & backend process manager
│   └── preload/index.js          # Secure contextBridge IPC
│
├── data/
│   └── demo_sales.csv            # Realistic enterprise sales dataset
│
├── tests/                        # Comprehensive test suite (22 tests)
│   ├── test_backend_startup.py
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   ├── test_reviewer.py
│   ├── test_file_validation.py
│   ├── test_api_endpoints.py
│   └── test_demo_scenario.py
│
├── scripts/                      # Windows launch and build batch scripts
│   ├── start-backend.bat
│   ├── start-dev.bat
│   └── build-win.bat
│
├── README.md
├── INSTALLATION.md
└── package.json                  # Root development & electron-builder orchestration
```

---

## ⚡ Quick Start

```powershell
# 1. Clone or navigate to workspace
cd "C:\Users\Krishna Verma\.gemini\antigravity\scratch\nexus-ai"

# 2. Setup backend virtual environment
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 3. Install dependencies
npm.cmd install
cd frontend && npm.cmd install && cd ..

# 4. Run automated test suite
.\backend\venv\Scripts\python.exe -m pytest tests -v

# 5. Launch the desktop application
npm.cmd run dev
```

---

## 🏆 Hackathon Demo Walkthrough

1. Open **NEXUS AI**.
2. Click the prominent amber **[Start Demo Workflow]** card on the dashboard.
3. Observe the live multi-agent execution pipeline in the Workspace:
   - **Data Analyst** computes summary metrics, regional breakdowns, and anomalies on `demo_sales.csv`.
   - **Research Agent** cross-references findings with external enterprise market trends.
   - **Risk Agent** assesses critical account churn and technical migration risks.
   - **Reviewer Agent** performs logical consistency auditing and approves deliverables.
   - **Report Agent** compiles a publication-ready strategic intelligence report.
4. Click **[View Full Report]** to inspect the 7-section deliverable or **[Download MD]** to export.
5. In the right dock, use the **Task Intelligence Chat** to ask:
   *"Why did revenue decline in Europe?"*
   Nexus AI will instantly deliver grounded answers based on the empirical results.

---

## 📜 License

MIT License © 2026 NEXUS AI Team.
