# Nexus AI — Shared Contracts & Types

This folder contains shared TypeScript type definitions, enums, constants, and API payload contracts shared across the frontend, backend, and desktop (Electron) layers of Nexus AI.

## Directory Structure
- `types/index.ts`: Strongly typed interfaces for Agents, Tasks, ChatMessages, SecurityTickets, ToolTraces, and SystemVitals.
- `constants/index.ts`: Default ports, URLs, agent roles, and agent descriptors.

## Usage
- **Frontend**: Directly imports from `shared/types` and `shared/constants` (or aliases mapped via `tsconfig.json`).
- **Desktop**: Imports types for IPC message safety.
- **Backend**: Pydantic models in `backend/app/schemas/` mirror these TypeScript contracts exactly, ensuring zero contract drift.
