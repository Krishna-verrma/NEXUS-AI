from fastapi import APIRouter, HTTPException
from typing import Any, Optional
from pydantic import BaseModel
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

class ImportIcsRequest(BaseModel):
    ics_content: str
    source_name: Optional[str] = "ics_import"

class CreateEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: Optional[str] = None
    location: Optional[str] = ""
    description: Optional[str] = ""
    category: Optional[str] = "meeting"
    source: Optional[str] = "google_calendar"

class UpdateEventRequest(BaseModel):
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    priority: Optional[str] = None
    join_url: Optional[str] = None
    is_important: Optional[int] = None

class SyncUrlRequest(BaseModel):
    url: str
    source_name: Optional[str] = "google_calendar"

# ── REST Endpoints requested by Section 10 ──

@router.get("/events")
def list_calendar_events(
    startDateTime: Optional[str] = None,
    endDateTime: Optional[str] = None,
    calendarId: Optional[str] = None,
    limit: int = 50
):
    events = CalendarService.get_events(
        start_datetime=startDateTime,
        end_datetime=endDateTime,
        calendar_id=calendarId,
        limit=limit
    )
    return {"events": events, "count": len(events)}

@router.post("/events")
async def create_calendar_event(req: CreateEventRequest):
    event = await CalendarService.create_event_async(
        title=req.title,
        start_time=req.start_time,
        end_time=req.end_time,
        location=req.location or "",
        description=req.description or "",
        category=req.category or "meeting",
        source=req.source or "google_calendar"
    )
    return {"event": event, "success": True}

@router.patch("/events/{event_id}")
async def update_calendar_event(event_id: str, req: UpdateEventRequest):
    updates = req.model_dump(exclude_unset=True)
    updated = await CalendarService.update_event_async(event_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"event": updated, "success": True}

@router.delete("/events/{event_id}")
async def delete_calendar_event(event_id: str):
    ok = await CalendarService.delete_event_async(event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "message": f"Event '{event_id}' deleted."}

# ── Legacy / Integration Endpoints ──

@router.get("/today")
def get_today_schedule():
    return CalendarService.get_today_schedule()

@router.get("/upcoming")
def get_upcoming_meetings(days: int = 7):
    return CalendarService.get_upcoming_meetings(days=days)

@router.get("/connectors")
def get_connectors():
    return CalendarService.get_connectors_status()

@router.post("/sync-url")
def sync_calendar_url(req: SyncUrlRequest):
    return CalendarService.sync_ics_url(req.url, req.source_name or "google_calendar")

@router.post("/scan-pc")
def scan_pc_calendar():
    return CalendarService.scan_local_pc_calendars()

@router.post("/import")
def import_ics(req: ImportIcsRequest):
    count = CalendarService.import_ics_content(req.ics_content, req.source_name or "ics_import")
    return {"message": f"Successfully imported {count} calendar events", "count": count}

@router.post("/clear-samples")
def clear_samples():
    count = CalendarService.clear_sample_events()
    return {"message": f"Cleared {count} sample demo events", "count": count}
