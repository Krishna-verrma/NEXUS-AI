import re
import json
import logging
from typing import Any, Optional
from datetime import datetime
from app.services.oauth.google_oauth import GoogleOAuthService
from app.database.repository import Repository

logger = logging.getLogger("nexus.integrations.google_calendar")

class GoogleCalendarIntegration:
    """
    Google Calendar Integration.
    Fetches real events from Google Calendar API, extracts Google Meet conference data,
    organizers, attendees, and formats them into a standardized structure.
    """

    @staticmethod
    async def fetch_events(start_iso: str, end_iso: str) -> list[dict[str, Any]]:
        raw_items = await GoogleOAuthService.fetch_calendar_events(start_iso, end_iso)
        normalized = []

        for item in raw_items:
            # Extract start and end time
            start_info = item.get("start", {})
            end_info = item.get("end", {})
            start_str = start_info.get("dateTime") or start_info.get("date") or ""
            end_str = end_info.get("dateTime") or end_info.get("date") or start_str

            # Clean ISO string to standard YYYY-MM-DD HH:MM:SS format
            clean_start = GoogleCalendarIntegration._clean_datetime(start_str)
            clean_end = GoogleCalendarIntegration._clean_datetime(end_str)

            # Organizer
            organizer_info = item.get("organizer", {})
            org_email = organizer_info.get("email", "")
            org_name = organizer_info.get("displayName") or org_email

            # Attendees
            raw_attendees = item.get("attendees", [])
            attendees = []
            for att in raw_attendees:
                attendees.append({
                    "name": att.get("displayName") or att.get("email", "Attendee"),
                    "email": att.get("email", "").lower(),
                    "responseStatus": att.get("responseStatus", "needsAction"),
                    "optional": bool(att.get("optional", False)),
                    "self": bool(att.get("self", False))
                })

            # Google Meet & Conference Data
            meet_url = None
            conf_data = item.get("conferenceData") or {}
            entry_points = conf_data.get("entryPoints", [])
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    meet_url = ep.get("uri")
                    break

            # If no conferenceData entrypoint, check hangoutLink or location / description
            if not meet_url:
                meet_url = item.get("hangoutLink")
            if not meet_url:
                full_text = f"{item.get('location', '')} {item.get('description', '')}"
                meet_match = re.search(r'https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}', full_text, re.IGNORECASE)
                if meet_match:
                    meet_url = meet_match.group(0)

            platform = "google_meet" if meet_url else ("in_person" if item.get("location") else "none")

            # Check if cancelled
            is_cancelled = item.get("status") == "cancelled"

            normalized.append({
                "id": f"gcal_{item.get('id')}",
                "provider_event_id": item.get("id"),
                "source": "google",
                "provider": "google-calendar",
                "title": item.get("summary", "Untitled Meeting"),
                "start": clean_start,
                "end": clean_end,
                "timezone": "Asia/Kolkata",
                "organizer": f"{org_name} <{org_email}>" if org_email else org_name,
                "organizer_email": org_email.lower(),
                "attendees": attendees,
                "location": item.get("location", ""),
                "description": item.get("description", ""),
                "meetingUrl": meet_url,
                "platform": platform,
                "conference_data": {
                    "conferenceId": conf_data.get("conferenceId"),
                    "solution": conf_data.get("conferenceSolution", {}).get("name", "Google Meet") if meet_url else None,
                    "entryPoints": entry_points,
                    "notes": conf_data.get("notes")
                },
                "status": "CANCELLED" if is_cancelled else "confirmed",
                "raw": item
            })

        return normalized

    @staticmethod
    def _clean_datetime(dt_str: str) -> str:
        if not dt_str:
            return ""
        # Handle simple date YYYY-MM-DD
        if len(dt_str) == 10 and "-" in dt_str:
            return f"{dt_str} 09:00:00"
        # Parse ISO format
        try:
            cleaned = dt_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return dt_str[:19].replace("T", " ")
