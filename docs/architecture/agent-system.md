# Nexus AI — Agent System & Orchestration

The Nexus agent architecture implements a hub-and-spoke multi-agent runtime.

## The 9 Autonomous Agents

1. **Nexus Orchestrator (`orchestrator/`)**:
   - Central intelligence.
   - Parses intent, formulates a multi-step execution plan, and routes to specialized agents.
   - Synthesizes findings into unified output.

2. **Computer Controller (`computer_agent/`)**:
   - Launches Windows applications (`notepad`, `calculator`, `chrome`, `explorer`, `terminal`, `code`).
   - Captures screenshots for visual inspection.
   - Monitors CPU, RAM, disk, and processes.

3. **Filesystem Operator (`file_agent/`)**:
   - Deep file search with wildcard patterns.
   - Safe file creation and inspection.
   - Protected file deletion through human authorization gates.

4. **Web Navigator (`web_agent/`)**:
   - Queries search engines and summarizes online sources.
   - Extracts page contents and validates technical documentation.

5. **Code Architect (`coding_agent/`)**:
   - Inspects AST, complexity, and syntax.
   - Sandboxed Python execution and test runners.

6. **Productivity Executive (`productivity_agent/`)**:
   - Manages calendar schedules and agenda blocks.
   - Resolves meeting conflicts and formats morning briefings.

7. **Comms Dispatcher (`communication_agent/`)**:
   - Drafts executive emails, team announcements, and notification messages.

8. **Data Scientist (`data_agent/`)**:
   - Analyzes CSV, JSON, and spreadsheet datasets.
   - Generates tabular metrics and calculates statistical summaries.

9. **Creative Studio (`creative_agent/`)**:
   - Drafts long-form concept documents, markdown publications, and pitch copy.

## Execution Flow
```
User Query
   ↓
Nexus Orchestrator (Intent Analysis)
   ↓
Planner (Step Decomposition)
   ↓
Specialized Agent (Tool Invocation)
   ↓
Security Gate Check (Pass or Request Permission Ticket)
   ↓
Telemetry Broadcast via WebSocket
   ↓
Orchestrator Synthesis
   ↓
Streamed Response to UI
```
