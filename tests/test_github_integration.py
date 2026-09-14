import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_github_connectors_status():
    resp = client.get("/api/calendar/connectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "github" in data
    assert "name" in data["github"]
    assert "connected" in data["github"]
    assert "events_count" in data["github"]

def test_github_test_connection_endpoint():
    resp = client.post("/api/settings/test-github", json={"token": "demo_test_token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "login" in data
    assert data["login"] == "demo-developer"

def test_github_sync_endpoint():
    resp = client.post("/api/settings/sync-github", json={"token": "demo_test_token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["count"] >= 1
