from enum import Enum
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"

# Defined operations that require human-in-the-loop review
SENSITIVE_OPERATIONS = {
    "delete_file": RiskLevel.HIGH,
    "execute_command": RiskLevel.CRITICAL,
    "modify_system_setting": RiskLevel.HIGH,
    "kill_process": RiskLevel.HIGH,
    "execute_code_sandbox": RiskLevel.MEDIUM,
    "send_external_email": RiskLevel.MEDIUM,
}

def is_operation_sensitive(operation_name: str) -> bool:
    return operation_name in SENSITIVE_OPERATIONS

def get_operation_risk(operation_name: str) -> RiskLevel:
    return SENSITIVE_OPERATIONS.get(operation_name, RiskLevel.LOW)

def create_security_ticket(
    operation_name: str,
    description: str,
    command_or_payload: str,
    agent_role: str,
) -> Dict[str, Any]:
    risk = get_operation_risk(operation_name)
    ticket_id = f"sec-{uuid.uuid4().hex[:8]}"
    return {
        "id": ticket_id,
        "riskLevel": risk.value,
        "operationName": operation_name,
        "description": description,
        "commandOrPayload": command_or_payload,
        "agentRole": agent_role,
        "status": TicketStatus.PENDING.value,
        "createdAt": datetime.utcnow().isoformat(),
        "resolvedAt": None,
    }
