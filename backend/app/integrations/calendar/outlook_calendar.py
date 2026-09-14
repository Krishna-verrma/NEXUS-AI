import re
import json
import logging
from typing import Any, Optional
from datetime import datetime
from app.services.oauth.microsoft_oauth import MicrosoftOAuthService

logger = logging.getLogger("nexus.integrations.outlook_calendar")

class OutlookCalendarIntegration:
    """
    Microsoft Outlook / Office 365 Calendar Integration using Microsoft Graph.
    Normalizes events, extracts Microsoft Teams meetings, attendees, and organizers.
    """

    @staticmethod
    async def fetch_events(start_iso: str, end_iso: str) -> list[dict[str, Any]]:
        raw_items = await MicrosoftOAuthService.fetch_calendar_events(start_iso, end_iso)
        normalized = []

        for item in raw_items:
            start_info = item.get("start", {})
            end_info = item.get("end", {})
            start_str = start_info.get("dateTime", "")
            end_str = end_info.get("dateTime", start_str)

            clean_start = OutlookCalendarIntegration._clean_datetime(start_str)
            clean_end = OutlookCalendarIntegration._clean_datetime(end_str)

            organizer_info = item.get("organizer", {}).get("emailAddress", {})
            org_email = organizer_info.get("address", "").lower()
            org_name = organizer_info.get("name") or org_email

            raw_attendees = item.get("attendees", [])
            attendees = []
            for att in raw_attendees:
                att_info = att.get("emailAddress", {})
                status_info = att.get("status", {})
                attendees.append({
                    "name": att_info.get("name") or att_info.get("address", "Attendee"),
                    "email": att_info.get("address", "").lower(),
                    "responseStatus": status_info.get("response", "none"),
                    "optional": att.get("type", "").lower() == "optional"
                })

            # Teams & Online Meeting Links
            teams_url = item.get("onlineMeetingUrl") or item.get("onlineMeeting", {}).get("joinUrl")
            if not teams_url:
                body_text = item.get("bodyPreview", "")
                teams_match = re.search(r'https?://teams\.microsoft\.com/l/meetup-join/[^\s"<>]+', body_text, re.IGNORECASE)
                if teams_match:
                    teams_url = teams_match.group(0)

            platform = "teams" if teams_url or item.get("isOnlineMeeting") else "in_person"
            is_cancelled = bool(item.get("isCancelled", False))

            normalized.append({
                "id": f"ms_{item.get('id')}",
                "provider_event_id": item.get("id"),
                "source": "outlook",
                "provider": "outlook",
                "title": item.get("subject", "Untitled Meeting"),
                "start": clean_start,
                "end": clean_end,
                "timezone": "Asia/Kolkata",
                "organizer": f"{org_name} <{org_email}>" if org_email else org_name,
                "organizer_email": org_email,
                "attendees": attendees,
                "location": item.get("location", {}).get("displayName", ""),
                "description": item.get("bodyPreview", ""),
                "meetingUrl": teams_url,
                "platform": platform,
                "conference_data": {
                    "isOnlineMeeting": item.get("isOnlineMeeting", False),
                    "solution": "Microsoft Teams" if platform == "teams" else None,
                    "joinUrl": teams_url
                },
                "status": "CANCELLED" if is_cancelled else "confirmed",
                "raw": item
            })

        return normalized

    @staticmethod
    def _clean_datetime(dt_str: str) -> str:
        if not dt_str:
            return ""
        if len(dt_str) == 10 and "-" in dt_str:
            return f"{dt_str} 09:00:00"
        try:
            cleaned = dt_str.split(".")[0].replace("Z", "")
            return cleaned.replace("T", " ")
        except Exception:
            return dt_str[:19].replace("T", " ")
