import re
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from app.database.repository import Repository
from app.integrations.calendar.google_calendar import GoogleCalendarIntegration
from app.integrations.calendar.outlook_calendar import OutlookCalendarIntegration

logger = logging.getLogger("nexus.integrations.unified_calendar")

class UnifiedCalendarEngine:
    """
    Unified Calendar Engine with:
    - Normalization across Google Calendar, Outlook, and Email intelligence.
    - Strict Deduplication preventing duplicate entries across providers.
    - Ownership Verification: Checks if user is actually attendee or organizer.
    - Personal Meeting Status: MY_MEETING, INVITED, OPTIONAL, ORGANIZER, NOT_MY_MEETING, EMAIL_ONLY, CANCELLED, RESCHEDULED.
    - Overlapping Conflict Detection.
    - Meeting Discrepancy Flagging (detecting reschedules from emails).
    """

    @staticmethod
    def get_user_emails() -> set[str]:
        """Collect all emails belonging to the user from connected accounts and settings."""
        emails = set()
        connected = Repository.list_connected_accounts()
        for acc in connected:
            if acc.get("account_email"):
                emails.add(acc["account_email"].strip().lower())

        # Also check stored settings
        db_settings = Repository.get_all_settings()
        g_url = db_settings.get("google_calendar_url", "")
        if "calendar.google.com/calendar/ical/" in g_url:
            m = re.search(r'/ical/([^/]+)/', g_url)
            if m:
                unquoted = m.group(1).replace("%40", "@").lower()
                if "@" in unquoted:
                    emails.add(unquoted)

        o_url = db_settings.get("outlook_calendar_url", "")
        if "outlook.office365.com/owa/calendar/" in o_url:
            m = re.search(r'/calendar/([^/]+)/', o_url)
            if m:
                unquoted = m.group(1).replace("%40", "@").lower()
                if "@" in unquoted:
                    emails.add(unquoted)

        # Common username fallback if empty
        if not emails:
            emails.add("krishnavermaam213@gmail.com")

        return emails

    @staticmethod
    async def sync_all_calendars(start_iso: Optional[str] = None, end_iso: Optional[str] = None) -> dict[str, Any]:
        """
        Fetch real events from connected Google and Outlook accounts,
        deduplicate, verify ownership, detect conflicts, and persist in SQLite.
        """
        now = datetime.now()
        s_iso = start_iso or (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        e_iso = end_iso or (now + timedelta(days=30)).strftime("%Y-%m-%d 23:59:59")

        user_emails = UnifiedCalendarEngine.get_user_emails()
        logger.info(f"Synchronizing calendars for verified user accounts: {user_emails}")

        # Fetch from providers
        google_events = []
        try:
            google_events = await GoogleCalendarIntegration.fetch_events(s_iso, e_iso)
        except Exception as e:
            logger.warning(f"Google Calendar fetch error: {e}")

        outlook_events = []
        try:
            outlook_events = await OutlookCalendarIntegration.fetch_events(s_iso, e_iso)
        except Exception as e:
            logger.warning(f"Outlook Calendar fetch error: {e}")

        all_raw_events = google_events + outlook_events
        logger.info(f"Retrieved {len(google_events)} Google events and {len(outlook_events)} Outlook events.")

        # 1. Deduplicate & Verify Ownership
        processed_events = UnifiedCalendarEngine.process_and_deduplicate(all_raw_events, user_emails)

        # 2. Conflict Detection
        UnifiedCalendarEngine.detect_calendar_conflicts(processed_events)

        # 3. Email Discrepancy Detection
        UnifiedCalendarEngine.cross_reference_emails(processed_events)

        # 4. Save to Repository
        saved_count = 0
        for ev in processed_events:
            Repository.upsert_calendar_event(ev)
            saved_count += 1

        # Record last sync time
        Repository.set_sync_state("last_calendar_sync", now.strftime("%Y-%m-%d %H:%M:%S"))

        return {
            "success": True,
            "total_synced": saved_count,
            "google_count": len(google_events),
            "outlook_count": len(outlook_events),
            "conflicts_detected": sum(1 for e in processed_events if e.get("is_conflict")),
            "sync_time": now.strftime("%Y-%m-%d %H:%M:%S")
        }

    @staticmethod
    def process_and_deduplicate(events: list[dict[str, Any]], user_emails: set[str]) -> list[dict[str, Any]]:
        """
        Merge duplicates across Google and Outlook, then assign strict ownership status.
        """
        deduped: list[dict[str, Any]] = []

        for ev in events:
            norm_title = re.sub(r'[^a-z0-9]', '', ev.get("title", "").lower())
            start_str = ev.get("start") or ev.get("start_time") or ""

            # Check if this matches an already added event (same normalized title and near same start time)
            matched = False
            for existing in deduped:
                ex_norm_title = re.sub(r'[^a-z0-9]', '', existing.get("title", "").lower())
                ex_start = existing.get("start") or existing.get("start_time") or ""

                if norm_title == ex_norm_title and norm_title != "":
                    # Compare start times within 10 minutes
                    if UnifiedCalendarEngine._times_are_close(start_str, ex_start, max_minutes_diff=10):
                        matched = True
                        # Merge meeting url / platform if missing
                        if not existing.get("meetingUrl") and ev.get("meetingUrl"):
                            existing["meetingUrl"] = ev["meetingUrl"]
                            existing["platform"] = ev.get("platform")
                        
                        # Normalize existing attendees to list
                        ex_att = existing.get("attendees")
                        if isinstance(ex_att, str):
                            try:
                                existing["attendees"] = json.loads(ex_att)
                            except Exception:
                                existing["attendees"] = []
                        elif not isinstance(ex_att, list):
                            existing["attendees"] = []

                        # Normalize ev attendees to list
                        ev_att = ev.get("attendees")
                        if isinstance(ev_att, str):
                            try:
                                ev_att = json.loads(ev_att)
                            except Exception:
                                ev_att = []
                        elif not isinstance(ev_att, list):
                            ev_att = []

                        existing_emails = {a.get("email") for a in existing["attendees"] if isinstance(a, dict)}
                        for att in ev_att:
                            if isinstance(att, dict) and att.get("email") not in existing_emails:
                                existing["attendees"].append(att)
                        break

            if not matched:
                deduped.append(dict(ev))

        # Determine ownership and personal status for each event
        for ev in deduped:
            UnifiedCalendarEngine._evaluate_event_ownership(ev, user_emails)

        return deduped

    @staticmethod
    def _evaluate_event_ownership(ev: dict[str, Any], user_emails: set[str]) -> None:
        """
        Determine if the user is organizer, attendee, invited, optional, or not invited.
        Assigns ownership_role and personal status.
        """
        # If already marked cancelled
        if ev.get("status") == "CANCELLED":
            ev["ownership_role"] = "attendee"
            ev["ownership_status"] = "CANCELLED"
            return

        org_email = (ev.get("organizer_email") or "").lower().strip()
        raw_att = ev.get("attendees")
        if isinstance(raw_att, str):
            try:
                attendees = json.loads(raw_att)
            except Exception:
                attendees = []
        elif isinstance(raw_att, list):
            attendees = raw_att
        else:
            attendees = []

        # Is user the organizer?
        is_organizer = any(ue in org_email for ue in user_emails) if org_email else False

        # Is user in attendees list?
        user_att_entry = None
        for att in attendees:
            if isinstance(att, dict):
                a_email = (att.get("email") or "").lower().strip()
                if any(ue in a_email for ue in user_emails):
                    user_att_entry = att
                    break

        if is_organizer:
            ev["ownership_role"] = "organizer"
            ev["status"] = "ORGANIZER"  # Also categorized as MY_MEETING in queries
        elif user_att_entry:
            resp_status = (user_att_entry.get("responseStatus") or "").lower()
            is_optional = user_att_entry.get("optional", False)

            if resp_status == "declined":
                ev["ownership_role"] = "declined"
                ev["status"] = "NOT_MY_MEETING"
            elif is_optional:
                ev["ownership_role"] = "optional"
                ev["status"] = "OPTIONAL"
            elif resp_status in ("accepted",):
                ev["ownership_role"] = "attendee"
                ev["status"] = "MY_MEETING"
            else:
                ev["ownership_role"] = "invited"
                ev["status"] = "INVITED"
        elif ev.get("source") in ("google", "outlook") and not attendees:
            # Personal calendar entry created without other attendees
            ev["ownership_role"] = "organizer"
            ev["status"] = "MY_MEETING"
        else:
            ev["ownership_role"] = "external"
            ev["status"] = "NOT_MY_MEETING"

        # Set ownership_status matching status
        ev["ownership_status"] = ev.get("status", "NOT_MY_MEETING")

    @staticmethod
    def detect_calendar_conflicts(events: list[dict[str, Any]]) -> None:
        """
        Detect overlapping meetings where user is expected to attend both.
        """
        # Filter for confirmed/invited meetings
        active_meetings = [
            e for e in events 
            if e.get("status") in ("MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER")
        ]

        for i in range(len(active_meetings)):
            m1 = active_meetings[i]
            s1 = m1.get("start") or m1.get("start_time")
            e1 = m1.get("end") or m1.get("end_time") or s1

            for j in range(i + 1, len(active_meetings)):
                m2 = active_meetings[j]
                s2 = m2.get("start") or m2.get("start_time")
                e2 = m2.get("end") or m2.get("end_time") or s2

                if s1 and e1 and s2 and e2:
                    try:
                        dt_s1 = datetime.strptime(s1[:19], "%Y-%m-%d %H:%M:%S")
                        dt_e1 = datetime.strptime(e1[:19], "%Y-%m-%d %H:%M:%S")
                        dt_s2 = datetime.strptime(s2[:19], "%Y-%m-%d %H:%M:%S")
                        dt_e2 = datetime.strptime(e2[:19], "%Y-%m-%d %H:%M:%S")

                        # Overlap condition: start1 < end2 and start2 < end1
                        if dt_s1 < dt_e2 and dt_s2 < dt_e1:
                            m1["is_conflict"] = 1
                            m1["conflict_with_id"] = m2.get("id")
                            m2["is_conflict"] = 1
                            m2["conflict_with_id"] = m1.get("id")
                    except Exception:
                        pass

    @staticmethod
    def cross_reference_emails(events: list[dict[str, Any]]) -> None:
        """
        Analyze emails for meeting reschedules, cancellations, or updates.
        If a discrepancy is detected (e.g. Email says 'moved to 4 PM'), flag the meeting.
        """
        recent_emails = Repository.get_important_emails(limit=25)
        if not recent_emails:
            return

        for ev in events:
            ev_title = ev.get("title", "").lower()
            for em in recent_emails:
                subj = em.get("subject", "").lower()
                snippet = em.get("snippet", "").lower()
                combined = f"{subj} {snippet}"

                # Match if subject contains the meeting title
                if ev_title and len(ev_title) > 3 and (ev_title in subj or ev_title in snippet):
                    # Check for reschedule signals
                    if any(w in combined for w in ("rescheduled", "moved to", "postponed", "new time", "shifted")):
                        time_match = re.search(r'\b(?:at|to)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b', combined, re.IGNORECASE)
                        if time_match:
                            new_time_hint = time_match.group(1)
                            ev["discrepancy_note"] = f"MEETING CHANGE DETECTED: Email from {em.get('sender', 'organizer')} mentions this meeting was moved to {new_time_hint}."
                        else:
                            ev["discrepancy_note"] = f"MEETING CHANGE DETECTED: Email from {em.get('sender', 'organizer')} indicates a reschedule or time change."
                        ev["status"] = "RESCHEDULED"
                        ev["ownership_status"] = "RESCHEDULED"
                    elif any(w in combined for w in ("cancelled", "canceled", "called off")):
                        ev["discrepancy_note"] = f"MEETING CANCELLATION DETECTED: Email from {em.get('sender', 'organizer')} states this meeting was cancelled."
                        ev["status"] = "CANCELLED"
                        ev["ownership_status"] = "CANCELLED"

    @staticmethod
    def _times_are_close(t1_str: str, t2_str: str, max_minutes_diff: int = 10) -> bool:
        if not t1_str or not t2_str:
            return False
        try:
            dt1 = datetime.strptime(t1_str[:19], "%Y-%m-%d %H:%M:%S")
            dt2 = datetime.strptime(t2_str[:19], "%Y-%m-%d %H:%M:%S")
            diff = abs((dt1 - dt2).total_seconds())
            return diff <= (max_minutes_diff * 60)
        except Exception:
            return t1_str[:16] == t2_str[:16]
