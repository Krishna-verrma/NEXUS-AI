import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import init_db
from app.database.repository import Repository

client = TestClient(app)

def test_startup_and_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "NEXUS AI"
    assert "version" in data

def test_system_agents_seeded():
    agents = Repository.list_agents()
    assert len(agents) >= 7
    agent_ids = [a["id"] for a in agents]
    assert "orchestrator" in agent_ids
    assert "data_analyst" in agent_ids
    assert "research" in agent_ids
    assert "coding" in agent_ids
    assert "document" in agent_ids
    assert "risk" in agent_ids
    assert "reviewer" in agent_ids
    assert "report" in agent_ids
