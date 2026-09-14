import sys
import os
import json
import pytest
from datetime import datetime, timedelta

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.crypto import encrypt_token, decrypt_token
from app.database.connection import init_db, db_session
from app.database.repository import Repository
from app.ai.model_router import model_router
from app.integrations.calendar.unified_calendar import UnifiedCalendarEngine
from app.ai.planner import AIPlanner
from app.services.chat_service import ChatService


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure database schema is initialized and clear calendar events before each test."""
    init_db()
    with db_session() as conn:
        conn.execute("DELETE FROM calendar_events")
        conn.execute("DELETE FROM email_metadata")
        conn.execute("DELETE FROM connected_accounts")
        conn.execute("DELETE FROM oauth_tokens")
    yield
    with db_session() as conn:
        conn.execute("DELETE FROM connected_accounts")
        conn.execute("DELETE FROM oauth_tokens")


# ── TEST 1: TOKEN ENCRYPTION & DECRYPTION ──
def test_token_encryption_decryption():
    raw_token = "ya29.a0AfH6SMC_secret_google_access_token_12345"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token


# ── TEST 2: REPOSITORY CRUD FOR CONNECTED ACCOUNTS & TOKENS ──
def test_connected_accounts_and_tokens():
    # Save Google account
    acc = Repository.save_connected_account(
        provider="google",
        account_email="testuser@gmail.com",
        account_name="Test User",
        scopes=["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/gmail.readonly"]
    )
    assert acc["provider"] == "google"
    assert acc["account_email"] == "testuser@gmail.com"

    # Save encrypted tokens
    tok = Repository.save_oauth_tokens(
        account_id=acc["id"],
        provider="google",
        access_token="test_access_token_abc",
        refresh_token="test_refresh_token_xyz",
        expires_at=(datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    )

    # Read back decrypted tokens
    retrieved_tok = Repository.get_oauth_tokens_by_provider("google")
    assert retrieved_tok is not None
    assert retrieved_tok["access_token"] == "test_access_token_abc"
    assert retrieved_tok["refresh_token"] == "test_refresh_token_xyz"


# ── TEST 3: UNIFIED CALENDAR ENGINE - DEDUPLICATION ──
def test_unified_calendar_deduplication():
    engine = UnifiedCalendarEngine()
    now_str = datetime.now().strftime("%Y-%m-%d 10:00:00")
    end_str = datetime.now().strftime("%Y-%m-%d 10:30:00")

    # Meeting from Google Calendar
    google_event = {
        "id": "g_evt_1",
        "title": "Quarterly Product Review",
        "start_time": now_str,
        "end_time": end_str,
        "organizer": "alice@company.com",
        "organizer_email": "alice@company.com",
        "attendees": [{"email": "krishna@company.com", "name": "Krishna Verma", "responseStatus": "accepted"}],
        "join_url": "https://meet.google.com/abc-defg-hij",
        "source": "google"
    }

    # Same meeting from Outlook Calendar (different source/ID, same normalized title/time)
    outlook_event = {
        "id": "ms_evt_1",
        "title": "Quarterly Product Review",
        "start_time": now_str,
        "end_time": end_str,
        "organizer": "alice@company.com",
        "organizer_email": "alice@company.com",
        "attendees": [{"email": "krishna@company.com", "name": "Krishna Verma", "responseStatus": "accepted"}],
        "join_url": "https://meet.google.com/abc-defg-hij",
        "source": "outlook"
    }

    processed = engine.process_and_deduplicate(
        [google_event, outlook_event],
        {"krishna@company.com"}
    )

    # Must be deduplicated to exactly 1 event
    assert len(processed) == 1
    assert processed[0]["title"] == "Quarterly Product Review"
    assert processed[0]["status"] in ("MY_MEETING", "INVITED")


# ── TEST 4: OWNERSHIP VERIFICATION & EMAIL-ONLY FILTERING ──
def test_ownership_verification_and_email_only():
    engine = UnifiedCalendarEngine()
    now_str = datetime.now().strftime("%Y-%m-%d 14:00:00")
    end_str = datetime.now().strftime("%Y-%m-%d 14:30:00")

    # Meeting where user is an attendee
    my_meeting = {
        "id": "meet_mine",
        "title": "Client Architecture Alignment",
        "start_time": now_str,
        "end_time": end_str,
        "organizer": "manager@company.com",
        "organizer_email": "manager@company.com",
        "attendees": [{"email": "krishna@company.com", "name": "Krishna", "responseStatus": "accepted"}],
        "source": "google"
    }

    # Meeting where user is neither organizer nor attendee
    not_my_meeting = {
        "id": "meet_other",
        "title": "Finance Team Internal Sync",
        "start_time": now_str,
        "end_time": end_str,
        "organizer": "cfo@company.com",
        "organizer_email": "cfo@company.com",
        "attendees": [{"email": "accountant@company.com", "name": "Accountant"}],
        "source": "google"
    }

    processed = engine.process_and_deduplicate(
        [my_meeting, not_my_meeting],
        {"krishna@company.com"}
    )

    # Only MY_MEETING should be returned for confirmed schedule
    my_events = [e for e in processed if e.get("status") in ("MY_MEETING", "INVITED", "ORGANIZER")]
    assert len(my_events) == 1
    assert my_events[0]["title"] == "Client Architecture Alignment"

    # Verify not_my_meeting was classified as NOT_MY_MEETING
    other = [e for e in processed if e.get("id") == "meet_other"]
    assert len(other) == 1
    assert other[0]["status"] == "NOT_MY_MEETING"


# ── TEST 5: CONFLICT DETECTION ──
def test_calendar_conflict_detection():
    engine = UnifiedCalendarEngine()
    # Two overlapping meetings
    event_a = {
        "id": "evt_overlap_a",
        "title": "Design Sprint Review",
        "start_time": "2026-09-14 11:00:00",
        "end_time": "2026-09-14 12:00:00",
        "organizer": "krishna@company.com",
        "organizer_email": "krishna@company.com",
        "source": "google"
    }
    event_b = {
        "id": "evt_overlap_b",
        "title": "Emergency Vendor Call",
        "start_time": "2026-09-14 11:30:00",
        "end_time": "2026-09-14 12:30:00",
        "organizer": "vendor@external.com",
        "organizer_email": "vendor@external.com",
        "attendees": [{"email": "krishna@company.com", "responseStatus": "accepted"}],
        "source": "google"
    }

    processed = engine.process_and_deduplicate(
        [event_a, event_b],
        {"krishna@company.com"}
    )
    engine.detect_calendar_conflicts(processed)

    conflicts = [e for e in processed if e.get("is_conflict")]
    assert len(conflicts) == 2


# ── TEST 6: AI BRAIN & MODEL ROUTER GROQ ──
@pytest.mark.asyncio
async def test_groq_ai_brain_routing():
    assert model_router.provider == "groq"
    assert model_router.model == "openai/gpt-oss-120b"
    assert "groq.com" in model_router.base_url

    # Test complete using Groq client
    try:
        res = await model_router.complete(
            messages=[{"role": "user", "content": "Respond with the single word: ONLINE"}]
        )
        assert res is not None
        assert len(res.strip()) > 0
    except RuntimeError as e:
        if "401" in str(e) or "Invalid API Key" in str(e):
            pytest.skip("Groq API key is not valid in test environment.")
        raise


# ── TEST 7: 13 EXACT USER QUERY TEST CASES ──
@pytest.mark.asyncio
async def test_13_exact_user_queries():
    # Setup mock connected accounts and verified test meetings in SQLite
    acc = Repository.save_connected_account(
        provider="google",
        account_email="krishna@workspace.com",
        account_name="Krishna Verma"
    )
    Repository.save_oauth_tokens(
        account_id=acc["id"],
        provider="google",
        access_token="active_test_token"
    )

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # Insert a real verified meeting for today (upcoming relative to now)
    future_start = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    future_end = (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")

    Repository.save_calendar_event({
        "id": "test_meet_today_1",
        "title": "NEXUS AI Architecture Alignment",
        "start_time": future_start,
        "end_time": future_end,
        "organizer": "Krishna Verma",
        "attendees": json.dumps([
            {"name": "Krishna Verma", "email": "krishna@workspace.com", "responseStatus": "accepted"},
            {"name": "Dev Lead", "email": "devlead@workspace.com", "responseStatus": "accepted"}
        ]),
        "platform": "google_meet",
        "join_url": "https://meet.google.com/nex-usai-mtg",
        "ownership_status": "MY_MEETING",
        "status": "MY_MEETING",
        "source": "google"
    })

    # Case 1: "Do I have a meeting today?"
    res1 = await AIPlanner.plan_and_execute("Do I have a meeting today?")
    assert "NEXUS AI Architecture Alignment" in res1.answer or "Yes" in res1.answer
    assert any("Google Calendar" in step for step in res1.steps)

    # Case 2: "What is my next meeting?"
    res2 = await AIPlanner.plan_and_execute("What is my next meeting?")
    assert "NEXUS AI Architecture Alignment" in res2.answer
    assert "Google Meet" in res2.answer or "Platform" in res2.answer

    # Case 3: "Show today's meetings."
    res3 = await AIPlanner.plan_and_execute("Show today's meetings.")
    assert "NEXUS AI Architecture Alignment" in res3.answer
    assert len(res3.steps) >= 2

    # Case 4: "Show tomorrow's meetings."
    res4 = await AIPlanner.plan_and_execute("Show tomorrow's meetings.")
    assert "tomorrow" in res4.answer.lower() or "scheduled" in res4.answer.lower()

    # Case 5: "What's my schedule this week?"
    res5 = await AIPlanner.plan_and_execute("What's my schedule this week?")
    assert "week" in res5.answer.lower() or "meeting" in res5.answer.lower()

    # Case 6: "Do I have any overlapping meetings?"
    res6 = await AIPlanner.plan_and_execute("Do I have any overlapping meetings?")
    assert "No calendar conflicts detected" in res6.answer or "conflict" in res6.answer.lower()

    # Case 7: "Who is attending my next meeting?"
    res7 = await AIPlanner.plan_and_execute("Who is attending my next meeting?")
    assert "Krishna Verma" in res7.answer or "Attendees" in res7.answer

    # Case 8: "Which meetings are Google Meet?"
    res8 = await AIPlanner.plan_and_execute("Which meetings are Google Meet?")
    assert "Google Meet" in res8.answer
    assert "https://meet.google.com/nex-usai-mtg" in res8.answer or "Join Meeting" in res8.answer

    # Case 9: "Which meetings are Teams?"
    # When Outlook is not connected:
    res9 = await AIPlanner.plan_and_execute("Which meetings are Teams?")
    assert "Outlook isn't connected yet" in res9.answer or "Teams" in res9.answer

    # Case 10: "Did anyone cancel my meeting?"
    res10 = await AIPlanner.plan_and_execute("Did anyone cancel my meeting?")
    assert "No cancelled meetings found" in res10.answer or "cancel" in res10.answer.lower()

    # Case 11: "Did anyone reschedule my meeting?"
    res11 = await AIPlanner.plan_and_execute("Did anyone reschedule my meeting?")
    assert "No rescheduled meetings detected" in res11.answer or "rescheduled" in res11.answer.lower()

    # Case 12: "Show important emails related to today's meetings."
    res12 = await AIPlanner.plan_and_execute("Show important emails related to today's meetings.")
    assert "email" in res12.answer.lower() or "unread" in res12.answer.lower() or "urgent" in res12.answer.lower()

    # Case 13: "What's my next meeting and give me the join link."
    res13 = await AIPlanner.plan_and_execute("What's my next meeting and give me the join link.")
    assert "NEXUS AI Architecture Alignment" in res13.answer
    assert "https://meet.google.com/nex-usai-mtg" in res13.answer or "Join Meeting" in res13.answer


# ── TEST 8: CHAT SERVICE INTEGRATION WITH AI PLANNER ──
@pytest.mark.asyncio
async def test_chat_service_workspace_query():
    now = datetime.now()
    future_start = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    future_end = (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")

    Repository.save_calendar_event({
        "id": "chat_test_meet_1",
        "title": "NEXUS AI Architecture Alignment",
        "start_time": future_start,
        "end_time": future_end,
        "organizer": "Krishna Verma",
        "attendees": json.dumps([{"name": "Krishna Verma", "email": "krishna@workspace.com"}]),
        "platform": "google_meet",
        "join_url": "https://meet.google.com/nex-usai-mtg",
        "ownership_status": "MY_MEETING",
        "status": "MY_MEETING",
        "source": "google"
    })

    chat_res = await ChatService.process_chat_message("What's my next meeting and give me the join link.")
    assert "answer" in chat_res or "content" in chat_res
    answer = chat_res.get("answer") or chat_res.get("content")
    assert "NEXUS AI Architecture Alignment" in answer
    assert "steps" in chat_res
    assert len(chat_res["steps"]) > 0


# ── TEST 9: GOOGLE CALENDAR RESCHEDULE ACTION MUTATION ──
@pytest.mark.asyncio
async def test_google_calendar_reschedule_action():
    from app.services.calendar_service import CalendarService
    
    # Setup test event
    now = datetime.now()
    initial_start = (now + timedelta(hours=2)).strftime("%Y-%m-%d 15:00:00")
    initial_end = (now + timedelta(hours=3)).strftime("%Y-%m-%d 16:00:00")

    Repository.save_calendar_event({
        "id": "gcal_action_test_1",
        "provider_event_id": "action_test_1",
        "title": "Strategy Alignment Call",
        "start_time": initial_start,
        "end_time": initial_end,
        "organizer": "Krishna Verma",
        "source": "google",
        "status": "MY_MEETING",
        "ownership_status": "MY_MEETING"
    })

    # User asks to move/reschedule the meeting to 5 PM
    res = await AIPlanner.plan_and_execute("Move my meeting to 5 PM")
    assert "Rescheduled in Google Calendar" in res.answer or "Strategy Alignment Call" in res.answer
    assert any("Google Calendar" in s for s in res.steps)

    # Verify event was updated in the repository
    updated = CalendarService.get_event_by_id("gcal_action_test_1")
    assert updated is not None
    assert "17:00:00" in updated["start_time"]


# ── TEST 10: GOOGLE CALENDAR CREATE ACTION MUTATION ──
@pytest.mark.asyncio
async def test_google_calendar_create_action():
    from app.services.calendar_service import CalendarService

    # User asks to schedule a new meeting
    res = await AIPlanner.plan_and_execute("Schedule a meeting tomorrow at 4 PM called Nexus Architecture Sync")
    assert "Nexus Architecture Sync" in res.answer
    assert "Created in Google Calendar" in res.answer or "Confirmed" in res.answer
    assert any("Google Calendar" in s for s in res.steps)

    # Verify event was created
    events = Repository.get_calendar_events(limit=20)
    matching = [e for e in events if "Nexus Architecture Sync" in e.get("title", "")]
    assert len(matching) >= 1
    assert "16:00:00" in matching[0]["start_time"]


# ── TEST 11: GOOGLE GMAIL OAUTH CONFIG & STATUS ──
def test_google_gmail_oauth_and_connector_status():
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # 1. Configure OAuth credentials via /api/auth/config/google
    conf_res = client.post("/api/auth/config/google", json={
        "client_id": "test_client_id_123.apps.googleusercontent.com",
        "client_secret": "GOCSPX_test_secret_abc",
        "redirect_uri": "http://127.0.0.1:8000/api/auth/callback/google"
    })
    assert conf_res.status_code == 200
    assert conf_res.json()["success"] is True

    # 2. Get status: both /google and /gmail should reflect client_id and redirect_uri
    status_res = client.get("/api/auth/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "gmail" in status_data
    assert status_data["gmail"]["name"] == "Gmail"
    assert status_data["gmail"]["client_id"] == "test_client_id_123.apps.googleusercontent.com"
    assert status_data["google"]["client_id"] == "test_client_id_123.apps.googleusercontent.com"

    # 3. Connectors status should include gmail
    conn_res = client.get("/api/calendar/connectors")
    assert conn_res.status_code == 200
    conn_data = conn_res.json()
    assert "gmail" in conn_data
    assert conn_data["gmail"]["name"] == "Google Gmail"

    # 4. Login endpoint alias should return auth url
    login_res = client.get("/api/auth/login/google")
    assert login_res.status_code == 200
    assert "url" in login_res.json()
    assert "accounts.google.com" in login_res.json()["url"]

    # 5. Test Gmail query endpoint returns valid structure
    test_gmail_res = client.get("/api/auth/google/test-gmail")
    assert test_gmail_res.status_code == 200
    assert "success" in test_gmail_res.json()

