# Nexus AI — Frontend Application

Modern React + TypeScript + Vite + Tailwind CSS frontend interface for Nexus AI.

## Architecture
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS + Custom futuristic glassmorphism design system
- **Icons**: Lucide React
- **Protocols**: REST API (`/api/*`) + WebSocket (`/api/ws`) for live streaming & telemetry
- **Pages**:
  - `Home/`: Command center with quick action triggers
  - `Chat/`: Multi-turn dialogue, tool call telemetry, and human-in-the-loop security approval cards
  - `Agents/`: 9 specialized agent cards with capability inspection
  - `Tasks/`: Background task queue and progress tracking
  - `Files/`: Workspace file explorer and preview
  - `Automations/`: Cron workflows and triggers
  - `Calendar/`: Agenda and event scheduling
  - `Activity/`: System audit and telemetry log
  - `Settings/`: Provider credentials, Demo Mode toggle, and security thresholds

## Running Independently
```bash
cd frontend
npm install
npm run dev
```
Runs at: http://localhost:5173
