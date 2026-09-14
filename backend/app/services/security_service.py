import datetime
from typing import Dict, Any, Optional
from app.core.security import TicketStatus
from app.database.session import SessionLocal
from app.models.audit import SecurityAuditLogModel

# Active in-memory tickets cache
_ACTIVE_TICKETS: Dict[str, Dict[str, Any]] = {}

def register_ticket(ticket: Dict[str, Any]):
    _ACTIVE_TICKETS[ticket["id"]] = ticket

def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    return _ACTIVE_TICKETS.get(ticket_id)

def list_pending_tickets() -> list:
    return [t for t in _ACTIVE_TICKETS.values() if t["status"] == TicketStatus.PENDING.value]

def resolve_ticket(ticket_id: str, decision: str) -> Optional[Dict[str, Any]]:
    ticket = _ACTIVE_TICKETS.get(ticket_id)
    if not ticket:
        return None

    status = TicketStatus.APPROVED.value if decision.lower() in ["approve", "allow", "yes"] else TicketStatus.REJECTED.value
    ticket["status"] = status
    ticket["resolvedAt"] = datetime.datetime.utcnow().isoformat()

    # Log to persistent audit table
    try:
        db = SessionLocal()
        audit_entry = SecurityAuditLogModel(
            ticket_id=ticket_id,
            operation_name=ticket.get("operationName", "unknown"),
            risk_level=ticket.get("riskLevel", "high"),
            agent_role=ticket.get("agentRole", "file_agent"),
            command_or_payload=ticket.get("commandOrPayload", ""),
            decision=status,
            details=f"User resolved ticket '{ticket_id}' with decision: {status}"
        )
        db.add(audit_entry)
        db.commit()
        db.close()
    except Exception as e:
        print(f"Failed to record audit log: {e}")

    return ticket
