# Nexus AI — API Specification

The FastAPI backend exposes RESTful endpoints and real-time WebSockets.

## Endpoints

### Chat
- `POST /api/chat`: Send a prompt for orchestration and agent execution.
  - Body: `{ "session_id": "...", "message": "...", "target_agent": "..." }`
- `GET /api/chat/sessions`: List active dialogue sessions.
- `GET /api/chat/sessions/{session_id}/messages`: Retrieve message history.

### Agents
- `GET /api/agents`: List all 9 specialized agents with descriptor metadata.
- `GET /api/agents/{role}`: Retrieve specific agent capabilities and status.
- `POST /api/agents/execute`: Execute a direct prompt against a specific agent.

### Tasks
- `GET /api/tasks`: List background tasks and progress.
- `POST /api/tasks`: Create an asynchronous task.
- `POST /api/tasks/{task_id}/cancel`: Cancel a running task.

### Files
- `GET /api/files`: Scan directory matching wildcard patterns.
- `GET /api/files/content`: Read content of a specific file.
- `POST /api/files`: Create or write a file.

### Automations
- `GET /api/automations`: List scheduled workflows.
- `POST /api/automations/{id}/toggle`: Enable or disable an automation.
- `POST /api/automations/{id}/trigger`: Trigger manual execution.

### System & Security
- `GET /api/system/health`: Service health and active agent count.
- `GET /api/system/vitals`: CPU, memory, uptime metrics.
- `GET /api/system/security/pending`: List pending security approval tickets.
- `POST /api/system/security/resolve`: Approve or reject a security ticket.
- `POST /api/system/settings`: Update API keys or toggle Demo Mode.

### WebSocket
- `WS /api/ws`: Bidirectional streaming channel for agent traces, token streaming, and security ticket broadcasts.
