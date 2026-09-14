import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database.repository import Repository
from app.services.calendar_service import CalendarService

import uuid
client = TestClient(app)

@pytest.fixture(scope="module")
def executive_briefing_task():
    CalendarService.seed_default_events()
    t_id = f"test-exec-briefing-{uuid.uuid4()}"
    task = Repository.create_task(
        task_id=t_id,
        title="Executive Briefing: Client Architecture Review",
        user_prompt="Prepare an executive briefing for my upcoming meeting: Client Architecture & Cloud Integration Review",
        complexity="moderate",
        is_demo=False
    )
    # Seed steps and final result
    Repository.update_task_status(
        task_id=t_id,
        status="completed",
        final_result=(
            "### Daily Agenda & Work Schedule\n"
            "**Briefing:** Today you have 2 key meetings and 2 deliverables.\n"
            "**📅 Scheduled Meetings Today:**\n"
            "- **14:00** — Client Architecture & Cloud Integration Review *(Zoom Video Conference)*\n"
            "**📋 Priority Work Deliverables:**\n"
            "- Deliverable: Complete database query optimization audit\n"
            "- Deliverable: Review and approve pull request #42\n"
        )
    )
    return Repository.get_task(t_id)

def test_chat_test_a_most_important_points(executive_briefing_task):
    """TEST A: 'What are the most important points?' -> Answer based on executive briefing."""
    payload = {
        "message": "What are the most important points?",
        "activeTaskId": executive_briefing_task["id"],
        "mode": "live"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ["TASK_FOLLOW_UP", "TASK_RELATED"]
    assert data["usedTaskContext"] is True
    assert "Based on the analysis performed for this task:" not in data["content"]
    assert any(k in data["content"].lower() for k in ["talking point", "objective", "milestone", "cloud", "architecture", "briefing"])

def test_chat_test_b_which_meeting_scheduled_today(executive_briefing_task):
    """TEST B: 'Which meeting is scheduled today?' -> Answer based on task/calendar context."""
    payload = {
        "message": "Which meeting is scheduled today?",
        "activeTaskId": executive_briefing_task["id"],
        "mode": "live"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ["TASK_RELATED", "TASK_FOLLOW_UP"]
    assert data["usedTaskContext"] is True
    assert "Based on the analysis performed for this task:" not in data["content"]
    assert any(k in data["content"].lower() for k in ["meeting", "client architecture", "14:00", "zoom"])

def test_chat_test_c_pm_of_india(executive_briefing_task):
    """TEST C: 'Who is the Prime Minister of India?' -> Answer actual question about India's PM. DO NOT mention executive briefing."""
    payload = {
        "message": "Who is the Prime Minister of India?",
        "activeTaskId": executive_briefing_task["id"],
        "mode": "live"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "GENERAL_QUESTION"
    assert data["usedTaskContext"] is False
    assert "Narendra Modi" in data["content"]
    # Verify complete context isolation: No mention of executive briefing, meetings, or calendar
    assert "executive briefing" not in data["content"].lower()
    assert "client architecture" not in data["content"].lower()
    assert "Based on the analysis performed for this task:" not in data["content"]

def test_chat_test_c_colloquial_pm_of_india(executive_briefing_task):
    """TEST C (variation): 'how is the pm of india' -> Answer actual question about India's PM."""
    payload = {
        "message": "how is the pm of india",
        "activeTaskId": executive_briefing_task["id"],
        "mode": "live"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "GENERAL_QUESTION"
    assert data["usedTaskContext"] is False
    assert "Narendra Modi" in data["content"]
    assert "executive briefing" not in data["content"].lower()
    assert "daily agenda" not in data["content"].lower()
    assert "Based on the analysis performed for this task:" not in data["content"]

def test_chat_test_d_what_is_python(executive_briefing_task):
    """TEST D: 'What is Python?' -> General Python explanation. DO NOT mention previous task."""
    payload = {
        "message": "What is Python?",
        "activeTaskId": executive_briefing_task["id"],
        "mode": "live"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "GENERAL_QUESTION"
    assert data["usedTaskContext"] is False
    assert any(k in data["content"].lower() for k in ["programming language", "guido van rossum", "syntax", "interpreted"])
    assert "executive briefing" not in data["content"].lower()
    assert "client architecture" not in data["content"].lower()
    assert "Based on the analysis performed for this task:" not in data["content"]

def test_chat_test_e_analyze_this_csv_creates_new_task(executive_briefing_task):
    """TEST E: 'Analyze this CSV.' -> Starts a NEW TASK rather than answering from executive briefing."""
    payload = {
        "message": "Analyze this CSV.",
        "activeTaskId": executive_briefing_task["id"],
        "mode": "live"
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "NEW_TASK"
    assert data["usedTaskContext"] is False
    assert data["newTaskId"] is not None
    assert data["newTaskId"] != executive_briefing_task["id"]
    assert "New Task Created" in data["content"]
    # Verify the new task was created in database
    new_t = Repository.get_task(data["newTaskId"])
    assert new_t is not None
    assert "Analyze this CSV" in new_t["user_prompt"]

def test_chat_ten_diverse_followup_intent_verifications(executive_briefing_task):
    """Verify at least 10 different follow-up questions correctly segregate context."""
    test_cases = [
        # (Message, Expected Intent, Expected usedTaskContext, Disallowed String)
        ("What is Docker?", "GENERAL_QUESTION", False, "executive briefing"),
        ("What is the capital of France?", "GENERAL_QUESTION", False, "executive briefing"),
        ("Why is this meeting important?", "TASK_RELATED", True, None),
        ("What were the key deliverables?", "TASK_FOLLOW_UP", True, None),
        ("What did you mean by risk?", "CLARIFICATION", True, None),
        ("Write a Python API for customer auth", "NEW_TASK", False, "executive briefing"),
        ("Research NVIDIA", "NEW_TASK", False, "executive briefing"),
        ("What should we do next?", "TASK_FOLLOW_UP", True, None),
        ("Summarize the findings.", "TASK_FOLLOW_UP", True, None),
        ("Tell me a joke", "GENERAL_QUESTION", False, "executive briefing"),
    ]

    for msg, exp_intent, exp_ctx, disallowed in test_cases:
        resp = client.post("/api/chat", json={
            "message": msg,
            "activeTaskId": executive_briefing_task["id"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == exp_intent, f"Failed on '{msg}': Expected {exp_intent}, got {data['intent']}"
        assert data["usedTaskContext"] is exp_ctx, f"Failed on '{msg}': Expected context {exp_ctx}, got {data['usedTaskContext']}"
        assert "Based on the analysis performed for this task:" not in data["content"]
        if disallowed:
            assert disallowed not in data["content"].lower(), f"Failed on '{msg}': Found leaked '{disallowed}'"
