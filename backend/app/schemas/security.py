from pydantic import BaseModel
from typing import Optional

class SecurityTicketResponse(BaseModel):
    id: str
    riskLevel: str
    operationName: str
    description: str
    commandOrPayload: str
    agentRole: str
    status: str
    createdAt: str
    resolvedAt: Optional[str] = None

class SecurityResolutionRequest(BaseModel):
    ticket_id: str
    decision: str # approved or rejected
