import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.calendar_service import CalendarService
from app.agents.schedule import ScheduleAgent
from app.agents.orchestrator import NexusOrchestrator
from app.services.chat_service import ChatService
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_calendar_service_today():
    schedule = CalendarService.get_today_schedule()
    assert "date" in schedule
    assert "day_of_week" in schedule
    assert "meetings" in schedule
    assert isinstance(schedule["meetings"], list)
    assert "work_tasks" in schedule
    assert isinstance(schedule["work_tasks"], list)

@pytest.mark.asyncio
async def test_calendar_service_upcoming():
    upcoming = CalendarService.get_upcoming_meetings(days=7)
    assert isinstance(upcoming, list)
    assert len(upcoming) >= 1

@pytest.mark.asyncio
async def test_schedule_agent_run():
    agent = ScheduleAgent()
    context = {"prompt": "Do I have work today or any meeting in coming ahead?"}
    res = await agent.run(context)
    assert res.success is True
    assert res.agent_id == "schedule"
    assert "today_meetings" in res.output
    assert "summary" in res.output
    assert "Yes" in res.output["summary"]
    assert len(res.output["today_meetings"]) > 0

@pytest.mark.asyncio
async def test_orchestrator_dynamic_schedule_routing():
    orchestrator = NexusOrchestrator()
    plan = await orchestrator.plan_workflow(
        prompt="Do I have work today or any meeting in coming ahead?",
        files=[]
    )
    agent_ids = [p["agent_id"] for p in plan]
    assert "schedule" in agent_ids
    assert "reviewer" in agent_ids

@pytest.mark.asyncio
async def test_chat_meeting_query():
    resp = await ChatService.process_chat_message(
        message="Do I have work today or any meeting coming ahead?"
    )
    assert resp["role"] == "assistant"
    assert "Today's Meetings:" in resp["content"] or "Your Schedule for Today" in resp["content"]

def test_api_calendar_today_endpoint():
    resp = client.get("/api/calendar/today")
    assert resp.status_code == 200
    data = resp.json()
    assert "meetings" in data
    assert len(data["meetings"]) >= 1

def test_evaluate_event_metadata():
    meta_urgent = CalendarService.evaluate_event_metadata(
        "URGENT: Executive Board Meeting",
        "Discussion on critical Q3 revenue goals https://meet.google.com/abc-defg-hij",
        "Google Meet"
    )
    assert meta_urgent["priority"] == "high"
    assert meta_urgent["is_important"] == 1
    assert meta_urgent["platform"] == "google_meet"
    assert meta_urgent["join_url"] == "https://meet.google.com/abc-defg-hij"

    meta_zoom = CalendarService.evaluate_event_metadata(
        "Sprint Triage",
        "Join link: https://zoom.us/j/123456789?pwd=test",
        "Online"
    )
    assert meta_zoom["platform"] == "zoom"
    assert meta_zoom["join_url"] == "https://zoom.us/j/123456789?pwd=test"

def test_api_calendar_connectors_endpoint():
    resp = client.get("/api/calendar/connectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "outlook" in data
    assert "google_calendar" in data
    assert "local_pc" in data
    assert "events_count" in data["outlook"]

def test_api_calendar_scan_pc_endpoint():
    resp = client.post("/api/calendar/scan-pc")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert "found_files" in data
    assert "imported_events" in data

