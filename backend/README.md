# Nexus AI — Backend Service

Modular, production-ready Python FastAPI backend powering the Nexus AI assistant.

## Features
- **FastAPI Core**: RESTful API endpoints, WebSockets for streaming responses and agent telemetry.
- **Independent AI Agents**: 9 modular agents + Orchestrator, each in its own dedicated package.
- **Isolated Tools**: Categorized modular tools (filesystem, computer, browser, code, calendar, documents, system).
- **Human-in-the-Loop Security**: Sensitive tools request permission tickets via WebSockets; actions cannot execute without user approval.
- **Multi-Provider LLM & Zero-Key Demo Mode**: Works with Gemini, OpenAI, Anthropic, or 100% locally in Demo Mode.
- **SQLite Database**: Persistent chat history, task queue, automations, and security audit log.

## Running Independently
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
API Documentation: http://localhost:8000/docs
WebSocket Endpoint: ws://localhost:8000/api/ws
Health Check: http://localhost:8000/api/system/health

## Running Tests
```bash
pytest
```
