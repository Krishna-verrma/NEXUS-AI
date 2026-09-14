import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_agents_endpoint():
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert isinstance(agents, list)
    assert len(agents) >= 7

def test_toggle_agent_endpoint():
    resp = client.put("/api/agents/coding/toggle", json={"is_enabled": False})
    assert resp.status_code == 200
    assert resp.json()["is_enabled"] is False

    # Restore
    resp = client.put("/api/agents/coding/toggle", json={"is_enabled": True})
    assert resp.status_code == 200
    assert resp.json()["is_enabled"] is True

def test_get_settings_endpoint():
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "ai_provider" in data
    assert "demo_mode" in data
    assert "google_calendar_url" in data
    assert "outlook_calendar_url" in data
    assert "auto_scan_pc" in data
    assert "web_search_api_key" in data

def test_update_settings_endpoint():
    payload = {
        "ai_provider": "gemini",
        "google_calendar_url": "https://calendar.google.com/calendar/ical/test/private/basic.ics",
        "outlook_calendar_url": "webcal://outlook.office365.com/test.ics",
        "auto_scan_pc": True,
        "enable_web_search": True
    }
    resp = client.post("/api/settings", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_provider"] == "gemini"
    assert data["google_calendar_url"] == "https://calendar.google.com/calendar/ical/test/private/basic.ics"
    assert data["outlook_calendar_url"] == "webcal://outlook.office365.com/test.ics"
    assert data["auto_scan_pc"] is True
    assert data["enable_web_search"] is True

def test_chat_endpoint():
    resp = client.post("/api/chat", json={"message": "Why did revenue decline in Europe?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    assert len(data["content"]) > 20

def test_reports_endpoint():
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
