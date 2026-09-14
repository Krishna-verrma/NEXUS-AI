import datetime
from typing import Dict, Any, List

# Simulated calendar state
_CALENDAR_EVENTS = [
    {
        "id": "evt-1",
        "title": "Nexus Architecture Review",
        "startTime": "14:00",
        "endTime": "15:00",
        "date": datetime.date.today().isoformat(),
        "attendees": ["team@nexus-ai.dev"],
        "status": "confirmed"
    },
    {
        "id": "evt-2",
        "title": "Agent Pipeline Sync",
        "startTime": "16:30",
        "endTime": "17:00",
        "date": datetime.date.today().isoformat(),
        "attendees": ["lead@nexus-ai.dev"],
        "status": "confirmed"
    }
]

def list_calendar_events(date_str: str = None) -> Dict[str, Any]:
    """List calendar events for a given day."""
    target_date = date_str or datetime.date.today().isoformat()
    matched = [e for e in _CALENDAR_EVENTS if e["date"] == target_date]
    return {
        "date": target_date,
        "count": len(matched),
        "events": matched
    }

def schedule_calendar_event(title: str, start_time: str, end_time: str, date_str: str = None) -> Dict[str, Any]:
    """Schedule a new event on the calendar."""
    target_date = date_str or datetime.date.today().isoformat()
    new_event = {
        "id": f"evt-{len(_CALENDAR_EVENTS) + 1}",
        "title": title,
        "startTime": start_time,
        "endTime": end_time,
        "date": target_date,
        "attendees": ["user@nexus.local"],
        "status": "confirmed"
    }
    _CALENDAR_EVENTS.append(new_event)
    return {
        "success": True,
        "event": new_event,
        "message": f"Successfully scheduled '{title}' for {target_date} from {start_time} to {end_time}."
    }
