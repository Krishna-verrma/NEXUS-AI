from fastapi import APIRouter, HTTPException
from app.services.automation_engine import list_automations, toggle_automation, trigger_automation_now

router = APIRouter(prefix="/api/automations", tags=["Automations"])

@router.get("")
def get_all_automations():
    return list_automations()

@router.post("/{automation_id}/toggle")
def toggle_automation_status(automation_id: str):
    res = toggle_automation(automation_id)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res

@router.post("/{automation_id}/trigger")
def trigger_automation(automation_id: str):
    res = trigger_automation_now(automation_id)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res
