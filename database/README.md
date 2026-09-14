# Nexus AI — Database Layer

Isolated database management layer for Nexus AI.

## Architecture
- **Engine**: SQLite via SQLAlchemy ORM.
- **Default Database File**: `backend/nexus.db` (git-ignored).
- **Models**:
  - `ChatSessionModel` & `ChatMessageModel` (`backend/app/models/chat.py`)
  - `AgentModel` & `AgentExecutionLogModel` (`backend/app/models/agent.py`)
  - `TaskModel` & `TaskStepModel` (`backend/app/models/task.py`)
  - `AutomationModel` (`backend/app/models/automation.py`)
  - `SecurityAuditLogModel` (`backend/app/models/audit.py`)

## Seeding
To populate seed data manually:
```bash
python database/seeds/seed_data.py
```
