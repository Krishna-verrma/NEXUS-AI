import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

client = TestClient(app)

def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Nexus AI"
    assert data["status"] == "operational"

def test_system_health():
    resp = client.get("/api/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["activeAgents"] == 9

def test_list_agents():
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) == 9

def test_chat_endpoint():
    resp = client.post("/api/chat", json={"message": "Write a python hello world function"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["sender"] == "assistant"
    assert "content" in data
    assert len(data["activityTraces"]) > 0

def test_tasks_endpoint():
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 1
