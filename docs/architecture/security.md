# Nexus AI — Security & Human-in-the-Loop Engine

Nexus AI enforces strict human authorization for sensitive desktop and system operations.

## Risk Categories

| Operation | Risk Level | Protection Mechanism |
| :--- | :--- | :--- |
| `delete_file` | HIGH | Interactive UI Confirmation Ticket |
| `execute_command` | CRITICAL | Interactive UI Confirmation Ticket |
| `kill_process` | HIGH | Interactive UI Confirmation Ticket |
| `execute_code_sandbox` | MEDIUM | Sandboxed builtins + UI confirmation |
| `send_external_email` | MEDIUM | UI confirmation |
| `search_files` / `read_file` | LOW | Auto-approved in standard mode |

## Ticket Resolution Flow
1. An agent requests a high-risk tool execution.
2. The tool dispatcher generates a unique ticket (`sec-xxxxxxxx`) with status `PENDING`.
3. The backend returns `waiting_approval` and broadcasts the ticket via WebSocket.
4. The UI displays an interactive security modal with the exact command/target.
5. The user clicks **[Cancel]** or **[Allow]**.
6. The decision is committed to the persistent `security_audit_logs` table.
