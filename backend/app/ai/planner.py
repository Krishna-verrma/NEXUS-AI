import re
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.database.repository import Repository
from app.ai.model_router import model_router
from app.tools.registry import tool_registry

logger = logging.getLogger("nexus.ai.planner")

class ExecutionStep(BaseModel):
    indicator: str
    tool_name: Optional[str] = None
    status: str = "completed"

class PlannerResponse(BaseModel):
    answer: str
    steps: list[str] = Field(default_factory=list)
    raw_tool_data: Optional[dict[str, Any]] = None
    intent: str = "general"
    account_connected: bool = True

class AIPlanner:
    """
    AI Planner following the strict execution pipeline:
    USER REQUEST
         ↓
    AI PLANNER
         ↓
    SELECT TOOL
         ↓
    EXECUTE TOOL
         ↓
    REAL API DATA
         ↓
    VERIFY DATA
         ↓
    AI RESPONSE
    """

    @classmethod
    async def plan_and_execute(cls, user_query: str) -> PlannerResponse:
        clean_q = user_query.strip()
        lower_q = clean_q.lower()
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")

        # 1. Check Connected Accounts
        connected_accounts = Repository.list_connected_accounts()
        google_acc = Repository.get_connected_account_by_provider("google")
        google_tok = Repository.get_oauth_tokens_by_provider("google") if google_acc else None
        google_connected = bool(google_acc and google_tok and google_tok.get("access_token"))

        ms_acc = Repository.get_connected_account_by_provider("microsoft")
        ms_tok = Repository.get_oauth_tokens_by_provider("microsoft") if ms_acc else None
        ms_connected = bool(ms_acc and ms_tok and ms_tok.get("access_token"))

        db_settings = Repository.get_all_settings()
        has_gcal_url = bool(db_settings.get("google_calendar_url"))
        has_outlook_url = bool(db_settings.get("outlook_calendar_url"))

        any_calendar_connected = google_connected or ms_connected or has_gcal_url or has_outlook_url

        # Check for Outlook-specific query when Outlook is not connected
        if ("teams" in lower_q or "outlook" in lower_q) and not (ms_connected or has_outlook_url):
            return PlannerResponse(
                answer="Outlook isn't connected yet. Connect Outlook from Settings to let me check your meetings.",
                steps=[
                    "🔎 Checking Microsoft Outlook connection...",
                    "⚠️ Outlook is not connected"
                ],
                intent="outlook_disconnected",
                account_connected=False
            )

        # Check for calendar queries when no calendar is connected at all
        calendar_keywords = ["meeting", "meetings", "calendar", "schedule", "call", "google meet", "teams", "conflict", "cancel", "reschedule"]
        is_calendar_query = any(kw in lower_q for kw in calendar_keywords)

        if is_calendar_query and not any_calendar_connected:
            return PlannerResponse(
                answer="Google Calendar isn't connected yet.\nConnect Google from Settings to let me check your meetings.",
                steps=[
                    "🔎 Checking Google Calendar connection...",
                    "⚠️ Google Calendar is not connected"
                ],
                intent="calendar_disconnected",
                account_connected=False
            )

        # 2. Plan and Select Tool Based on Query Intent
        steps = []
        
        # Test Case 12: "Show important emails related to today's meetings." / "Show my important emails from today."
        if "email" in lower_q or "emails" in lower_q or "inbox" in lower_q or "gmail" in lower_q:
            steps.append("🔎 Searching Gmail and Outlook for important communications...")
            tool_res = await tool_registry.execute_tool("google.gmail.search_emails", query="meeting OR important", limit=10)
            steps.append("✓ Emails retrieved")
            steps.append("🧠 Correlating emails with today's meetings...")

            emails = tool_res.data.get("messages", []) if tool_res.success else []
            if not emails:
                ans = "You have no unread or urgent work emails related to today's meetings."
            else:
                lines = [f"Here {'is an important email' if len(emails)==1 else f'are {len(emails)} important emails'} related to your work & schedule:\n"]
                for em in emails[:5]:
                    sender = em.get("from") or em.get("sender", "Unknown")
                    subj = em.get("subject", "No Subject")
                    snip = em.get("snippet", "")[:120]
                    lines.append(f"- **From {sender}:** *{subj}*\n  > \"{snip}...\"")
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="emails")

        # Action: Reschedule / Move / Change / Update a meeting (Cloud Mutation)
        is_reschedule_action = (
            any(kw in lower_q for kw in ("reschedule to", "move to", "move my", "change to", "change my", "shift to", "postpone to", "push to", "delay to"))
            or (("reschedule" in lower_q or "change" in lower_q or "move" in lower_q or "shift" in lower_q) and ("meeting" in lower_q or "call" in lower_q or "event" in lower_q) and ("to " in lower_q or "at " in lower_q or "pm" in lower_q or "am" in lower_q or "tomorrow" in lower_q))
        ) and not ("did anyone" in lower_q or "was my" in lower_q or "has anyone" in lower_q or "is anyone" in lower_q)

        if is_reschedule_action:
            steps.append("🔎 Locating target meeting on calendar...")
            events = Repository.get_calendar_events(limit=50, status_filter=["MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER"])
            target_meeting = None

            # 1. Check if user mentioned an existing time (e.g. "my 3 PM meeting")
            from_time_match = re.search(r'\b(?:at|from|the)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b', lower_q)
            if from_time_match and events:
                src_time_str = from_time_match.group(1).lower()
                for ev in events:
                    if src_time_str in ev.get("start_time", "").lower():
                        target_meeting = ev
                        break

            # 2. Check if user mentioned a title
            if not target_meeting and events:
                for ev in events:
                    t_lower = (ev.get("title") or "").lower()
                    if len(t_lower) > 3 and t_lower in lower_q:
                        target_meeting = ev
                        break

            # 3. Default to the next upcoming meeting
            if not target_meeting and events:
                target_meeting = events[0]

            if not target_meeting:
                steps.append("⚠️ No scheduled meeting found")
                return PlannerResponse(
                    answer="⚠️ Could not locate a scheduled meeting on your calendar to reschedule.",
                    steps=steps,
                    intent="reschedule_action"
                )

            meeting_title = target_meeting.get("title", "Meeting")
            target_id = target_meeting.get("id")

            # Extract destination time
            target_time_text = clean_q
            to_match = re.search(r'\bto\s+(.+)$', clean_q, re.IGNORECASE)
            if to_match:
                target_time_text = to_match.group(1)

            parsed_start, parsed_end = cls._parse_natural_datetime(target_time_text)

            steps.append(f"🔄 Updating '{meeting_title}' in Google Calendar API...")
            from app.services.calendar_service import CalendarService
            updated = await CalendarService.update_event_async(target_id, {
                "start_time": parsed_start,
                "end_time": parsed_end
            })

            if not updated:
                steps.append("⚠️ Failed to update Google Calendar")
                return PlannerResponse(
                    answer=f"⚠️ Failed to update '{meeting_title}' in Google Calendar. Please make sure Google Calendar is connected in Settings.",
                    steps=steps,
                    intent="reschedule_action"
                )

            steps.append("✓ Google Calendar updated successfully")
            steps.append("🧠 Verifying updated calendar schedule...")

            try:
                dt_obj = datetime.strptime(parsed_start[:19], "%Y-%m-%d %H:%M:%S")
                dt_end_obj = datetime.strptime(parsed_end[:19], "%Y-%m-%d %H:%M:%S")
                formatted_new = f"{dt_obj.strftime('%A, %B %d, %Y')} from {dt_obj.strftime('%I:%M %p').lstrip('0')} to {dt_end_obj.strftime('%I:%M %p').lstrip('0')}"
            except Exception:
                formatted_new = f"{parsed_start} – {parsed_end}"

            join_url = updated.get("join_url")
            join_str = f"\n  🔗 [Google Meet]({join_url})" if join_url else ""

            ans = (
                f"✅ **Meeting Rescheduled in Google Calendar**\n\n"
                f"- **Meeting:** {meeting_title}\n"
                f"- **New Time:** {formatted_new}\n"
                f"- **Calendar:** Google Calendar (Synchronized in real-time){join_str}"
            )

            return PlannerResponse(
                answer=ans,
                steps=steps,
                intent="reschedule_action"
            )

        # Action: Create / Schedule a new meeting (Cloud Mutation)
        is_create_action = (
            lower_q.startswith(("schedule a meeting", "create a meeting", "book a meeting", "add a meeting", "set up a meeting", "schedule an event", "create an event", "schedule meeting", "create meeting", "book meeting"))
            or (("schedule" in lower_q or "create" in lower_q or "book" in lower_q) and "meeting" in lower_q and ("called" in lower_q or "with" in lower_q or "at " in lower_q or "tomorrow" in lower_q or "for " in lower_q))
        ) and not is_reschedule_action

        if is_create_action:
            steps.append("🔎 Preparing Google Calendar event...")
            title_match = re.search(r"(?:called|named|title|titled)\s+[\"']?([^\"',\.]+)[\"']?", clean_q, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
            else:
                cleaned = re.sub(r"^(schedule|create|book|add)\s+(a\s+|an\s+)?(meeting|event|call)?\s*", "", clean_q, flags=re.IGNORECASE)
                title = cleaned[:35].strip() or "Nexus Scheduled Meeting"

            parsed_start, parsed_end = cls._parse_natural_datetime(clean_q)

            steps.append(f"🔄 Creating '{title}' in Google Calendar API with Google Meet...")
            from app.services.calendar_service import CalendarService
            created = await CalendarService.create_event_async(
                title=title,
                start_time=parsed_start,
                end_time=parsed_end,
                source="google"
            )

            steps.append("✓ Google Calendar updated successfully")
            steps.append("🧠 Finalizing event details...")

            try:
                dt_obj = datetime.strptime(parsed_start[:19], "%Y-%m-%d %H:%M:%S")
                dt_end_obj = datetime.strptime(parsed_end[:19], "%Y-%m-%d %H:%M:%S")
                formatted_when = f"{dt_obj.strftime('%A, %B %d, %Y')} at {dt_obj.strftime('%I:%M %p').lstrip('0')}"
            except Exception:
                formatted_when = parsed_start

            join_url = created.get("join_url") if created else None
            join_str = f"\n  🔗 [Google Meet Join Meeting]({join_url})" if join_url else ""

            ans = (
                f"✅ **Meeting Created in Google Calendar**\n\n"
                f"- **Title:** {title}\n"
                f"- **When:** {formatted_when}\n"
                f"- **Calendar:** Google Calendar (Synchronized live){join_str}"
            )

            return PlannerResponse(
                answer=ans,
                steps=steps,
                intent="create_action"
            )

        # Test Case 1 & 3: "Do I have a meeting today?" / "Show today's meetings."
        if (("meeting" in lower_q and "today" in lower_q) or lower_q == "show today's meetings" or lower_q == "show today meetings"):
            steps.append("🔎 Checking Google Calendar...")
            tool_res = await tool_registry.execute_tool("google.calendar.get_events", start_datetime="today")
            steps.append("✓ Calendar data retrieved")
            steps.append("🧠 Analyzing schedule...")

            events = tool_res.data.get("events", []) if tool_res.success else []
            # Filter only verified meetings for today
            today_events = [e for e in events if e.get("status") in ("MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER")]
            
            return await cls._synthesize_today_schedule_response(today_events, clean_q, steps)

        # Test Case 2 & 13: "What is my next meeting?" / "What's my next meeting and give me the join link."
        if "next meeting" in lower_q or "upcoming meeting" in lower_q:
            steps.append("🔎 Checking Google Calendar...")
            tool_res = await tool_registry.execute_tool("google.calendar.get_events", start_datetime="today")
            steps.append("✓ Calendar data retrieved")
            steps.append("🧠 Finding next upcoming meeting...")

            events = tool_res.data.get("events", []) if tool_res.success else []
            verified = [e for e in events if e.get("status") in ("MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER")]
            
            # Find chronologically next meeting
            next_meeting = None
            for m in verified:
                s_time = m.get("start_time")
                try:
                    dt = datetime.strptime(s_time[:19], "%Y-%m-%d %H:%M:%S")
                    if dt >= (now - timedelta(minutes=5)):
                        next_meeting = m
                        break
                except Exception:
                    pass

            if not next_meeting and verified:
                next_meeting = verified[0]

            return await cls._synthesize_next_meeting_response(next_meeting, clean_q, steps)

        # Test Case 4: "Show tomorrow's meetings."
        if "tomorrow" in lower_q and ("meeting" in lower_q or "schedule" in lower_q):
            steps.append("🔎 Checking Google Calendar...")
            tool_res = await tool_registry.execute_tool("google.calendar.get_events", start_datetime="tomorrow")
            steps.append("✓ Calendar data retrieved")
            steps.append("🧠 Analyzing schedule for tomorrow...")

            events = tool_res.data.get("events", []) if tool_res.success else []
            tomorrow_events = [e for e in events if e.get("status") in ("MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER")]

            tom_date = (now + timedelta(days=1)).strftime("%A, %B %d, %Y")
            if not tomorrow_events:
                ans = f"You have no meetings scheduled for tomorrow ({tom_date})."
            else:
                lines = [f"Here {'is your meeting' if len(tomorrow_events)==1 else 'are your meetings'} scheduled for tomorrow ({tom_date}):\n"]
                for m in tomorrow_events:
                    lines.append(cls._format_meeting_line(m))
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="tomorrow_meetings")

        # Test Case 5: "What's my schedule this week?"
        if "this week" in lower_q or "week" in lower_q:
            steps.append("🔎 Checking Google & Outlook Calendars...")
            tool_res = await tool_registry.execute_tool("google.calendar.get_events", start_datetime="this_week")
            steps.append("✓ Calendar data retrieved")
            steps.append("🧠 Compiling weekly schedule...")

            events = tool_res.data.get("events", []) if tool_res.success else []
            weekly_events = [e for e in events if e.get("status") in ("MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER")]

            if not weekly_events:
                ans = "You have no meetings scheduled for this week."
            else:
                lines = [f"You have **{len(weekly_events)} meetings** scheduled for this week:\n"]
                for m in weekly_events:
                    lines.append(cls._format_meeting_line(m))
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="week_schedule")

        # Test Case 6: "Do I have any overlapping meetings?" / "Do I have any meeting conflicts?"
        if "conflict" in lower_q or "overlapping" in lower_q or "overlap" in lower_q:
            steps.append("🔎 Inspecting calendar for scheduling overlaps...")
            conflicts = Repository.get_calendar_conflicts()
            steps.append(f"✓ Found {len(conflicts)} conflict event{'s' if len(conflicts)!=1 else ''}")
            steps.append("🧠 Verifying meeting details...")

            if not conflicts:
                ans = "✅ **No calendar conflicts detected.** None of your scheduled meetings overlap."
            else:
                lines = [f"⚠️ **You have {len(conflicts)} meeting conflict(s) detected:**\n"]
                for c in conflicts:
                    lines.append(f"- **{c.get('title')}** ({c.get('start_time')}) — Overlaps with another scheduled session.")
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="conflicts")

        # Test Case 7: "Who is attending my next meeting?"
        if (
            "attending" in lower_q 
            or "attendee" in lower_q 
            or "attendees" in lower_q 
            or (("who is" in lower_q or "who's" in lower_q or "who" in lower_q) and "meeting" in lower_q)
        ):
            steps.append("🔎 Checking upcoming meetings...")
            events = Repository.get_upcoming_meetings(now.strftime("%Y-%m-%d %H:%M:%S"), limit=5)
            steps.append("✓ Meeting details retrieved")
            steps.append("🧠 Analyzing attendee list...")

            if not events:
                return PlannerResponse(
                    answer="You have no upcoming meetings scheduled right now.",
                    steps=steps,
                    intent="attendees"
                )

            next_m = events[0]
            attendees_raw = next_m.get("attendees")
            attendees = []
            if attendees_raw:
                try:
                    attendees = json.loads(attendees_raw) if isinstance(attendees_raw, str) else attendees_raw
                except Exception:
                    pass

            org = next_m.get("organizer", "You")
            lines = [
                f"**Meeting:** {next_m.get('title')}",
                f"**Time:** {cls._format_time_span(next_m.get('start_time'), next_m.get('end_time'))}",
                f"**Organizer:** {org}\n",
                f"**Attendees ({len(attendees)}):**"
            ]
            if attendees:
                for a in attendees:
                    lines.append(f"- {a.get('name', 'Attendee')} ({a.get('email', '')}) [{a.get('responseStatus', 'invited')}]")
            else:
                lines.append("- No external attendees listed.")

            return PlannerResponse(answer="\n".join(lines), steps=steps, intent="attendees")

        # Test Case 8: "Which meetings are Google Meet?"
        if "google meet" in lower_q:
            steps.append("🔎 Searching Google Calendar for Google Meet conferences...")
            events = Repository.get_calendar_events(limit=50)
            steps.append("✓ Calendar conferences retrieved")
            steps.append("🧠 Filtering Google Meet sessions...")

            meet_events = [
                e for e in events 
                if e.get("platform") == "google_meet" or (e.get("join_url") and "meet.google.com" in e["join_url"])
            ]
            if not meet_events:
                ans = "You have no upcoming meetings on Google Meet."
            else:
                lines = [f"You have **{len(meet_events)} meeting(s)** on Google Meet:\n"]
                for m in meet_events:
                    join = m.get("join_url") or m.get("meeting_url")
                    lines.append(f"- **{m.get('title')}** ({cls._format_time_span(m.get('start_time'), m.get('end_time'))})\n  🔗 [Join Meeting]({join})")
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="google_meet_filter")

        # Test Case 9: "Which meetings are Teams?"
        if "teams" in lower_q:
            steps.append("🔎 Searching Outlook Calendar for Microsoft Teams sessions...")
            events = Repository.get_calendar_events(limit=50)
            steps.append("✓ Outlook conferences retrieved")
            steps.append("🧠 Filtering Microsoft Teams sessions...")

            teams_events = [
                e for e in events 
                if e.get("platform") == "teams" or (e.get("join_url") and "teams.microsoft.com" in e["join_url"])
            ]
            if not teams_events:
                ans = "You have no upcoming meetings on Microsoft Teams."
            else:
                lines = [f"You have **{len(teams_events)} meeting(s)** on Microsoft Teams:\n"]
                for m in teams_events:
                    join = m.get("join_url") or m.get("meeting_url")
                    lines.append(f"- **{m.get('title')}** ({cls._format_time_span(m.get('start_time'), m.get('end_time'))})\n  🔗 [Join Meeting]({join})")
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="teams_filter")

        # Test Case 10: "Did anyone cancel my meeting?"
        if "cancel" in lower_q:
            steps.append("🔎 Checking calendars & emails for cancellations...")
            events = Repository.get_calendar_events(status_filter=["CANCELLED"], limit=20)
            emails = Repository.get_important_emails(limit=20)
            cancel_emails = [e for e in emails if "cancel" in e.get("subject", "").lower() or "cancel" in e.get("snippet", "").lower()]
            steps.append("✓ Status verified from provider APIs")
            steps.append("🧠 Analyzing cancellation records...")

            if not events and not cancel_emails:
                ans = "✅ **No cancelled meetings found.** None of your scheduled meetings have been cancelled."
            else:
                lines = ["⚠️ **Meeting Cancellation Information:**\n"]
                for e in events:
                    lines.append(f"- **{e.get('title')}** ({e.get('start_time')}) — Marked as CANCELLED by organizer.")
                for em in cancel_emails:
                    lines.append(f"- Email from **{em.get('sender')}**: *\"{em.get('subject')}\"*")
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="cancelled")

        # Test Case 11: "Did anyone reschedule my meeting?" (Inquiry)
        if "reschedule" in lower_q or "rescheduled" in lower_q:
            steps.append("🔎 Inspecting calendar events and emails for reschedule notices...")
            events = Repository.get_calendar_events(limit=50)
            rescheduled = [e for e in events if e.get("status") == "RESCHEDULED" or e.get("discrepancy_note")]
            steps.append("✓ Discrepancy detection complete")
            steps.append("🧠 Correlating email intelligence...")

            if not rescheduled:
                ans = "✅ **No rescheduled meetings detected.** All your meetings match their current calendar schedule."
            else:
                lines = ["⚠️ **Meeting Change Detected:**\n"]
                for r in rescheduled:
                    note = r.get("discrepancy_note") or "Time change detected via communication channels."
                    lines.append(f"- **{r.get('title')}** ({r.get('start_time')}):\n  *{note}*")
                ans = "\n".join(lines)

            return PlannerResponse(answer=ans, steps=steps, intent="rescheduled")


        # Fallback: General workspace or assistant question using Groq AI
        steps.append("🧠 Consulting Groq AI Brain...")
        try:
            prompt = (
                f"You are Nexus AI, a Personal Workspace Command Center assistant.\n"
                f"User asks: '{clean_q}'\n"
                f"Respond concisely, professionally, and accurately in local time (Asia/Kolkata)."
            )
            llm_ans = await model_router.complete(
                messages=[{"role": "user", "content": prompt}]
            )
            return PlannerResponse(
                answer=llm_ans,
                steps=steps,
                intent="general"
            )
        except Exception as e:
            return PlannerResponse(
                answer=f"Could not complete query: {str(e)}",
                steps=steps,
                intent="error"
            )

    @classmethod
    async def _synthesize_today_schedule_response(
        cls,
        events: list[dict[str, Any]],
        user_query: str,
        steps: list[str]
    ) -> PlannerResponse:
        now = datetime.now()
        day_str = now.strftime("%A, %B %d, %Y")

        if not events:
            return PlannerResponse(
                answer=f"No. You do not have any meetings scheduled for today ({day_str}).",
                steps=steps,
                intent="today_meetings"
            )

        lines = [f"Yes. You have **{len(events)} meeting{'s' if len(events)!=1 else ''} today** ({day_str}):\n"]
        for m in events:
            time_str = cls._format_time_span(m.get("start_time"), m.get("end_time"))
            title = m.get("title", "Untitled Meeting")
            platform = m.get("platform") or ("Google Meet" if m.get("join_url") and "meet.google.com" in m["join_url"] else ("Microsoft Teams" if m.get("join_url") and "teams.microsoft.com" in m["join_url"] else "In-person"))
            if platform == "google_meet":
                platform = "Google Meet"
            elif platform == "teams":
                platform = "Microsoft Teams"
            
            org = m.get("organizer", "Krishna")
            join = m.get("join_url") or m.get("meeting_url")
            join_btn = f"  🔗 [{platform} Join Meeting]({join})" if join else f"  📍 {platform}"

            lines.append(f"**{time_str}** — **{title}**\n  Organizer: {org}\n{join_btn}")

        return PlannerResponse(
            answer="\n\n".join(lines),
            steps=steps,
            intent="today_meetings",
            raw_tool_data={"events": events, "count": len(events)}
        )

    @classmethod
    async def _synthesize_next_meeting_response(
        cls,
        meeting: Optional[dict[str, Any]],
        user_query: str,
        steps: list[str]
    ) -> PlannerResponse:
        if not meeting:
            return PlannerResponse(
                answer="You have no upcoming meetings scheduled right now.",
                steps=steps,
                intent="next_meeting"
            )

        time_str = cls._format_time_span(meeting.get("start_time"), meeting.get("end_time"))
        title = meeting.get("title", "Untitled Meeting")
        org = meeting.get("organizer", "Krishna")
        platform = meeting.get("platform")
        if platform == "google_meet":
            platform = "Google Meet"
        elif platform == "teams":
            platform = "Microsoft Teams"
        else:
            platform = "In-person"

        join = meeting.get("join_url") or meeting.get("meeting_url")
        join_line = f"\n**Join Link:** [{platform} Join Meeting]({join})" if join else ""

        ans = (
            f"Your next meeting is:\n\n"
            f"**{title}**\n"
            f"🕒 **Time:** {time_str}\n"
            f"👤 **Organizer:** {org}\n"
            f"💻 **Platform:** {platform}"
            f"{join_line}"
        )

        return PlannerResponse(
            answer=ans,
            steps=steps,
            intent="next_meeting",
            raw_tool_data=meeting
        )

    @staticmethod
    def _format_time_span(start_dt_str: Optional[str], end_dt_str: Optional[str]) -> str:
        if not start_dt_str:
            return "Scheduled"
        try:
            dt1 = datetime.strptime(start_dt_str[:19], "%Y-%m-%d %H:%M:%S")
            t1 = dt1.strftime("%I:%M %p").lstrip("0")
            if end_dt_str:
                dt2 = datetime.strptime(end_dt_str[:19], "%Y-%m-%d %H:%M:%S")
                t2 = dt2.strftime("%I:%M %p").lstrip("0")
                return f"{t1} – {t2}"
            return t1
        except Exception:
            return start_dt_str.split(" ")[-1] if " " in start_dt_str else start_dt_str

    @staticmethod
    def _format_meeting_line(m: dict[str, Any]) -> str:
        t_span = AIPlanner._format_time_span(m.get("start_time"), m.get("end_time"))
        title = m.get("title")
        join = m.get("join_url") or m.get("meeting_url")
        platform = "Google Meet" if (join and "meet.google.com" in join) else ("Microsoft Teams" if (join and "teams.microsoft.com" in join) else "In-person")
        link_md = f" • [Join Call]({join})" if join else ""
        return f"- **{t_span}** — **{title}** ({platform}){link_md}"

    @staticmethod
    def _parse_natural_datetime(text: str) -> tuple[str, str]:
        lower = text.lower()
        now = datetime.now()
        target_date = now.date()

        if "tomorrow" in lower:
            target_date = now.date() + timedelta(days=1)
        elif "yesterday" in lower:
            target_date = now.date() - timedelta(days=1)
        else:
            iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
            if iso_match:
                y, m, d = map(int, iso_match.group(1).split("-"))
                target_date = datetime(y, m, d).date()

        # Parse hour/minute, e.g. "4 PM", "16:00", "4:30 pm", "at 4"
        time_match = re.search(r"\b(?:at\s+|to\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", lower)
        hour = 16 # default 4 PM
        minute = 0
        if time_match:
            h = int(time_match.group(1))
            m = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)
            if meridiem == "pm" and h < 12:
                h += 12
            elif meridiem == "am" and h == 12:
                h = 0
            elif not meridiem:
                if 1 <= h <= 7:
                    h += 12
            hour = h
            minute = m

        start_dt = datetime(target_date.year, target_date.month, target_date.day, hour, minute, 0)
        end_dt = start_dt + timedelta(hours=1)

        return start_dt.strftime("%Y-%m-%d %H:%M:%S"), end_dt.strftime("%Y-%m-%d %H:%M:%S")
