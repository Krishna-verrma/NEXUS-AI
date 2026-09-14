from fastapi import APIRouter, HTTPException
from app.tools.computer.system_info import get_system_info
from app.core.config import settings
from app.schemas.system import SystemVitalsResponse, SettingsUpdateRequest
from app.schemas.security import SecurityResolutionRequest
from app.services.security_service import list_pending_tickets, resolve_ticket, get_ticket
from app.services.websocket_manager import ws_manager
from app.agents import AGENT_REGISTRY

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Nexus AI Backend",
        "version": settings.VERSION,
        "demoMode": settings.DEMO_MODE,
        "activeAgents": len(AGENT_REGISTRY)
    }

@router.get("/vitals", response_model=SystemVitalsResponse)
def get_vitals():
    sys_info = get_system_info()
    return SystemVitalsResponse(
        cpuUsagePercent=sys_info.get("cpuUsagePercent", 12.0),
        memoryUsagePercent=sys_info.get("memoryUsagePercent", 40.0),
        diskFreeGb=sys_info.get("diskFreeGb", 200.0),
        uptimeSeconds=sys_info.get("uptimeSeconds", 1200.0),
        isDemoMode=settings.DEMO_MODE,
        activeAgentsCount=len(AGENT_REGISTRY),
        activeTasksCount=3,
        backendVersion=settings.VERSION
    )

@router.get("/security/pending")
def get_pending_security_tickets():
    return list_pending_tickets()

@router.post("/security/resolve")
async def resolve_security_ticket(payload: SecurityResolutionRequest):
    ticket = resolve_ticket(payload.ticket_id, payload.decision)
    if not ticket:
        raise HTTPException(status_code=404, detail="Security ticket not found")
    
    # Broadcast ticket resolution over websocket
    await ws_manager.emit_security_ticket(ticket)
    return {
        "success": True,
        "ticket": ticket,
        "message": f"Ticket {payload.ticket_id} has been {ticket['status']}"
    }

@router.post("/settings")
def update_settings(payload: SettingsUpdateRequest):
    if payload.demo_mode is not None:
        settings.DEMO_MODE = payload.demo_mode
    if payload.gemini_api_key is not None:
        settings.GEMINI_API_KEY = payload.gemini_api_key
        if payload.gemini_api_key:
            settings.DEMO_MODE = False
    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key
        if payload.openai_api_key:
            settings.DEMO_MODE = False
    if payload.anthropic_api_key is not None:
        settings.ANTHROPIC_API_KEY = payload.anthropic_api_key
        if payload.anthropic_api_key:
            settings.DEMO_MODE = False
    if payload.auto_approve_safe_actions is not None:
        settings.AUTO_APPROVE_SAFE_ACTIONS = payload.auto_approve_safe_actions

    return {
        "success": True,
        "demoMode": settings.DEMO_MODE,
        "hasGeminiKey": bool(settings.GEMINI_API_KEY),
        "hasOpenAIKey": bool(settings.OPENAI_API_KEY),
        "hasAnthropicKey": bool(settings.ANTHROPIC_API_KEY),
    }
