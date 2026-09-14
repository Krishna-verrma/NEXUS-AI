from fastapi import APIRouter, HTTPException
from app.models.schemas import AgentResponse, AgentToggleRequest
from app.database.repository import Repository

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("", response_model=list[AgentResponse])
def list_agents():
    return Repository.list_agents()

@router.put("/{agent_id}/toggle", response_model=AgentResponse)
def toggle_agent(agent_id: str, req: AgentToggleRequest):
    updated = Repository.toggle_agent(agent_id, req.is_enabled)
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")
    return updated
