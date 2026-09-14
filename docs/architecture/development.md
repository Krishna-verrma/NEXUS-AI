# Nexus AI — Developer Guide

How to extend, build, and add new agents/tools to Nexus AI.

## How to Add a New Agent
1. Create a new directory in `backend/app/agents/<agent_name>/`.
2. Implement:
   - `prompts.py`: Define system prompt and specialized instructions.
   - `tools.py`: Define allowed tool imports.
   - `agent.py`: Inherit from `BaseAgent` and implement `execute()`.
3. Register the agent in `backend/app/agents/__init__.py` and in `orchestrator/agent.py`.
4. Add the agent role to `shared/types/index.ts` and `shared/constants/index.ts`.

## How to Add a New Tool
1. Create a tool file under `backend/app/tools/<domain>/<tool_name>.py`.
2. Register the tool function in `backend/app/tools/__init__.py` in `TOOL_REGISTRY`.
3. If the tool is destructive or executes shell commands, add it to `SENSITIVE_OPERATIONS` in `backend/app/core/security.py`.

## Running Local Tests
- **Backend Tests**:
  ```bash
  cd backend
  python -m pytest
  ```
- **Frontend Build**:
  ```bash
  cd frontend
  npm run build
  ```
