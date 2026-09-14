# Installation Guide - NEXUS AI

This document provides complete instructions for installing, configuring, running, and packaging **NEXUS AI** on Windows.

---

## 1. System Requirements

* **Operating System**: Windows 10 or Windows 11 (64-bit)
* **Node.js**: v18.0.0 or higher (v20+ recommended)
* **Python**: 3.10 to 3.14 (with `venv` and `pip`)
* **RAM**: 4 GB minimum (8 GB recommended)
* **Disk Space**: ~1.5 GB for dependencies and build artifacts

---

## 2. Quick Start (Zero-Configuration Demo Mode)

NEXUS AI includes an offline **Demo Mode** that requires no external API keys or cloud accounts.

### Step 1: Open Project Directory
Open PowerShell or Command Prompt in the `nexus-ai` root directory:
```powershell
cd "C:\Users\Krishna Verma\.gemini\antigravity\scratch\nexus-ai"
```

### Step 2: Setup Python Virtual Environment
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### Step 3: Install Node Dependencies
```powershell
# Install root packaging dependencies
npm.cmd install

# Install frontend UI dependencies
cd frontend
npm.cmd install
cd ..
```

### Step 4: Run Tests to Verify Environment
```powershell
.\backend\venv\Scripts\python.exe -m pytest tests -v
```
All 22 test suites should report `PASSED`.

---

## 3. Running in Development Mode

Run the complete stack (Backend + Vite Frontend + Electron Window) with a single command:

```powershell
npm.cmd run dev
```

Or double-click:
```
scripts\start-dev.bat
```

Alternatively, you can run services independently:

### Terminal 1 (FastAPI Backend):
```powershell
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation and Swagger UI will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Terminal 2 (React + Vite Web UI):
```powershell
cd frontend
npm.cmd run dev
```
Accessible in any modern browser at: [http://localhost:5173](http://localhost:5173)

### Terminal 3 (Electron Desktop Window):
```powershell
npm.cmd run dev:electron
```

---

## 4. Configuring Real AI Models

By default, NEXUS AI runs in **Demo Mode** with realistic deterministic mock intelligence. To connect a live LLM provider:

1. Launch NEXUS AI and click **Settings** in the left sidebar.
2. Toggle **Demo Mode** off.
3. Select your provider:
   - **OpenAI**: Input your `sk-...` key and select `gpt-4o` or `gpt-4o-mini`.
   - **Groq**: Base URL `https://api.groq.com/openai/v1`, Model `llama-3.1-70b-versatile`.
   - **OpenRouter**: Base URL `https://openrouter.ai/api/v1`, Model `anthropic/claude-3.5-sonnet`.
   - **Ollama (Local Offline)**: Base URL `http://localhost:11434/v1`, Model `llama3`.
   - **Custom OpenAI-Compatible Endpoint**: Any endpoint supporting `/v1/chat/completions`.
4. Click **Save Configuration**. Your API key is encrypted and stored strictly in the local SQLite database (`data/nexus_ai.db`). It is never exposed to the frontend or sent externally.

---

## 5. Building the Windows Desktop Installer

To produce a production Windows `.exe` installer (NSIS) or standalone portable application:

```powershell
# 1. Build the production React assets
npm.cmd run build:frontend

# 2. Package Windows installer
npm.cmd run build:win
```

Or double-click:
```
scripts\build-win.bat
```

The resulting executables will be generated in:
```
nexus-ai/release/
├── NEXUS AI Setup 1.0.0.exe   (NSIS Windows Installer)
└── NEXUS AI 1.0.0.exe         (Portable Standalone Executable)
```

### Installation Experience
1. Double-click `NEXUS AI Setup 1.0.0.exe`.
2. Choose installation folder (or accept standard default).
3. The installer creates desktop and Start Menu shortcuts.
4. Launching **NEXUS AI** automatically starts the background process supervisor, mounts the database, and launches the command center.

---

## 6. Troubleshooting

* **PowerShell script execution policy disabled**:
  If PowerShell complains that script execution is disabled, always call `npm.cmd` instead of `npm`, or run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
* **Port 8000 already in use**:
  If port 8000 is occupied by another local service, change `PORT=8001` in `backend/app/core/config.py` and the corresponding base URL in `frontend/src/services/api.ts` and `desktop/main/index.js`.
* **Missing Visual C++ Runtime**:
  If Python or SQLite throws a DLL error, install the [Microsoft Visual C++ Redistributable 2015-2022](https://aka.ms/vs/17/release/vc_redist.x64.exe).
