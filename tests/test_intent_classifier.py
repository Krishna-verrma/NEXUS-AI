import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.intent_classifier import IntentClassifier, IntentType

@pytest.fixture
def briefing_task():
    return {
        "id": "task-briefing-123",
        "title": "Executive Briefing for Upcoming Meeting",
        "user_prompt": "Prepare an executive briefing for my upcoming meeting: Client Architecture Review",
        "final_result": "Meeting: Client Architecture Review at 14:00.\nObjectives:\n1. Cloud Migration Milestones\n2. Security Governance\nRisks:\n- Latency SLA compliance\nKey Recommendations:\n- Accelerate phased canary rollout."
    }

def test_task_related_questions(briefing_task):
    intent, used_ctx = IntentClassifier.classify("Why is this meeting important?", briefing_task)
    assert intent == IntentType.TASK_RELATED
    assert used_ctx is True

    intent, used_ctx = IntentClassifier.classify("Which meeting is scheduled today?", briefing_task)
    assert intent == IntentType.TASK_RELATED
    assert used_ctx is True

def test_task_follow_up_questions(briefing_task):
    intent, used_ctx = IntentClassifier.classify("What are the most important points?", briefing_task)
    assert intent == IntentType.TASK_FOLLOW_UP
    assert used_ctx is True

    intent, used_ctx = IntentClassifier.classify("What were the key deliverables?", briefing_task)
    assert intent == IntentType.TASK_FOLLOW_UP
    assert used_ctx is True

    intent, used_ctx = IntentClassifier.classify("Summarize the findings.", briefing_task)
    assert intent == IntentType.TASK_FOLLOW_UP
    assert used_ctx is True

def test_general_questions(briefing_task):
    intent, used_ctx = IntentClassifier.classify("how is the pm of india", briefing_task)
    assert intent == IntentType.GENERAL_QUESTION
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("Who is the Prime Minister of India?", briefing_task)
    assert intent == IntentType.GENERAL_QUESTION
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("What is Python?", briefing_task)
    assert intent == IntentType.GENERAL_QUESTION
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("What is the capital of France?", briefing_task)
    assert intent == IntentType.GENERAL_QUESTION
    assert used_ctx is False

def test_new_task_requests(briefing_task):
    intent, used_ctx = IntentClassifier.classify("Analyze this CSV.", briefing_task)
    assert intent == IntentType.NEW_TASK
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("Analyze this new CSV", briefing_task)
    assert intent == IntentType.NEW_TASK
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("Write a Python API", briefing_task)
    assert intent == IntentType.NEW_TASK
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("Write me a C++ program.", briefing_task)
    assert intent == IntentType.NEW_TASK
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("Create a business plan", briefing_task)
    assert intent == IntentType.NEW_TASK
    assert used_ctx is False

    intent, used_ctx = IntentClassifier.classify("Research NVIDIA", briefing_task)
    assert intent == IntentType.NEW_TASK
    assert used_ctx is False

def test_clarification_requests(briefing_task):
    intent, used_ctx = IntentClassifier.classify("What did you mean by risk?", briefing_task)
    assert intent == IntentType.CLARIFICATION
    assert used_ctx is True
