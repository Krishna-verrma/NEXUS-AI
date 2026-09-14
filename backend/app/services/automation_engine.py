import datetime
from typing import List, Dict, Any
from app.agents import orchestrator
from app.database.session import SessionLocal
from app.models.automation import AutomationModel

# In-memory default automations for demo & production
DEFAULT_AUTOMATIONS = [
    {
        "id": "auto-1",
        "name": "Daily Executive Morning Briefing",
        "description": "Synthesizes today's agenda, unread communications, and system status at 09:00 AM.",
        "trigger_type": "cron",
        "trigger_schedule": "0 9 * * *",
        "enabled": True,
        "target_agent": "productivity_agent",
        "action_prompt": "Generate a concise morning briefing with scheduled agenda and task priorities.",
        "last_run": (datetime.datetime.utcnow() - datetime.timedelta(hours=4)).isoformat(),
        "next_run": (datetime.datetime.utcnow() + datetime.timedelta(hours=20)).isoformat(),
    },
    {
        "id": "auto-2",
        "name": "Workspace File Cleanup & Health Scan",
        "description": "Scans workspace directory for orphan temp files and indexes codebase.",
        "trigger_type": "cron",
        "trigger_schedule": "0 0 * * *",
        "enabled": True,
        "target_agent": "file_agent",
        "action_prompt": "Inspect workspace files and report storage distribution.",
        "last_run": (datetime.datetime.utcnow() - datetime.timedelta(hours=12)).isoformat(),
        "next_run": (datetime.datetime.utcnow() + datetime.timedelta(hours=12)).isoformat(),
    },
    {
        "id": "auto-3",
        "name": "Desktop Security & High-Load Watcher",
        "description": "Monitors CPU usage spikes above 85% and alerts user.",
        "trigger_type": "event",
        "trigger_schedule": "cpu > 85%",
        "enabled": True,
        "target_agent": "computer_agent",
        "action_prompt": "Check hardware vitals and notify user if thermal or process limits are reached.",
        "last_run": (datetime.datetime.utcnow() - datetime.timedelta(minutes=15)).isoformat(),
        "next_run": (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat(),
    }
]

def list_automations() -> List[Dict[str, Any]]:
    return DEFAULT_AUTOMATIONS

def toggle_automation(automation_id: str) -> Dict[str, Any]:
    for a in DEFAULT_AUTOMATIONS:
        if a["id"] == automation_id:
            a["enabled"] = not a["enabled"]
            return {"success": True, "automation": a}
    return {"success": False, "error": f"Automation {automation_id} not found"}

def trigger_automation_now(automation_id: str) -> Dict[str, Any]:
    for a in DEFAULT_AUTOMATIONS:
        if a["id"] == automation_id:
            a["last_run"] = datetime.datetime.utcnow().isoformat()
            res = orchestrator.execute(a["action_prompt"], context={"target_agent": a["target_agent"]})
            return {
                "success": True,
                "automation": a,
                "result": res.to_dict()
            }
    return {"success": False, "error": f"Automation {automation_id} not found"}
