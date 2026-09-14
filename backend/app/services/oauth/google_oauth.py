import os
import time
import json
import uuid
import logging
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import httpx

from app.core.config import settings
from app.database.repository import Repository

logger = logging.getLogger("nexus.oauth.google")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
GOOGLE_GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.readonly"
]

class GoogleOAuthService:
    @staticmethod
    def get_credentials() -> dict[str, str]:
        db_settings = Repository.get_all_settings()
        client_id = db_settings.get("google_client_id") or os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = db_settings.get("google_client_secret") or os.getenv("GOOGLE_CLIENT_SECRET", "")
        redirect_uri = db_settings.get("google_redirect_uri") or os.getenv(
            "GOOGLE_REDIRECT_URI", f"http://{settings.host}:{settings.port}/api/auth/google/callback"
        )
        return {
            "client_id": client_id.strip(),
            "client_secret": client_secret.strip(),
            "redirect_uri": redirect_uri.strip()
        }

    @staticmethod
    def set_credentials(client_id: str, client_secret: str, redirect_uri: Optional[str] = None) -> None:
        Repository.set_setting("google_client_id", client_id.strip())
        Repository.set_setting("google_client_secret", client_secret.strip())
        if redirect_uri:
            Repository.set_setting("google_redirect_uri", redirect_uri.strip())

    @staticmethod
    def generate_auth_url(redirect_uri: Optional[str] = None) -> dict[str, str]:
        creds = GoogleOAuthService.get_credentials()
        if not creds["client_id"]:
            raise ValueError("Google Client ID is not configured. Please enter it in Settings.")

        r_uri = redirect_uri or creds["redirect_uri"]
        params = {
            "client_id": creds["client_id"],
            "redirect_uri": r_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": f"nexus_g_{int(time.time())}"
        }
        url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return {"auth_url": url, "state": params["state"]}

    @staticmethod
    async def exchange_code_for_tokens(code: str, redirect_uri: Optional[str] = None) -> dict[str, Any]:
        creds = GoogleOAuthService.get_credentials()
        if not creds["client_id"] or not creds["client_secret"]:
            raise ValueError("Google Client ID and Secret must be configured.")

        r_uri = redirect_uri or creds["redirect_uri"]
        payload = {
            "code": code,
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "redirect_uri": r_uri,
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
            if resp.status_code != 200:
                logger.error(f"Google token exchange failed: {resp.text}")
                raise RuntimeError(f"Failed to exchange Google OAuth code: {resp.text}")
            token_data = resp.json()

            # Retrieve user info with access token
            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_email = "user@gmail.com"
            user_name = "Google User"
            if userinfo_resp.status_code == 200:
                u_info = userinfo_resp.json()
                user_email = u_info.get("email", user_email)
                user_name = u_info.get("name", user_name)

            account_id = f"google_{user_email.replace('@', '_').replace('.', '_')}"
            expires_in = token_data.get("expires_in", 3600)
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).strftime("%Y-%m-%d %H:%M:%S")

            # Save connected account and encrypted tokens in SQLite
            Repository.save_connected_account(
                account_id=account_id,
                provider="google",
                account_email=user_email,
                account_name=user_name,
                status="connected",
                scopes=SCOPES
            )
            Repository.save_oauth_tokens(
                account_id=account_id,
                provider="google",
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=expires_at,
                token_type=token_data.get("token_type", "Bearer")
            )

            return {
                "success": True,
                "account_id": account_id,
                "account_email": user_email,
                "account_name": user_name
            }

    @staticmethod
    async def get_valid_access_token(account_id: Optional[str] = None) -> Optional[str]:
        account = None
        if account_id:
            account = Repository.get_connected_account(account_id)
        else:
            account = Repository.get_connected_account_by_provider("google")

        if not account:
            return None

        tokens = Repository.get_oauth_tokens(account["id"])
        if not tokens or not tokens.get("access_token"):
            return None

        # Check token expiration
        expires_at_str = tokens.get("expires_at")
        is_expired = False
        if expires_at_str:
            try:
                exp_dt = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) >= (exp_dt - timedelta(minutes=5)):
                    is_expired = True
            except Exception:
                pass

        if not is_expired:
            return tokens["access_token"]

        # Refresh token if expired
        refresh_tok = tokens.get("refresh_token")
        if not refresh_tok:
            logger.warning(f"Google token for {account['account_email']} is expired and has no refresh token.")
            Repository.save_connected_account(account["id"], "google", account["account_email"], status="needs_reauth")
            return None

        creds = GoogleOAuthService.get_credentials()
        payload = {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": refresh_tok,
            "grant_type": "refresh_token"
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
            if resp.status_code == 200:
                new_data = resp.json()
                new_access = new_data["access_token"]
                expires_in = new_data.get("expires_in", 3600)
                new_exp = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).strftime("%Y-%m-%d %H:%M:%S")
                Repository.save_oauth_tokens(
                    account_id=account["id"],
                    provider="google",
                    access_token=new_access,
                    refresh_token=new_data.get("refresh_token") or refresh_tok,
                    expires_at=new_exp
                )
                Repository.save_connected_account(account["id"], "google", account["account_email"], status="connected")
                return new_access
            else:
                logger.error(f"Failed to refresh Google token: {resp.text}")
                Repository.save_connected_account(account["id"], "google", account["account_email"], status="needs_reauth")
                return None

    @staticmethod
    async def fetch_calendar_events(
        time_min: str,
        time_max: str,
        account_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        access_token = await GoogleOAuthService.get_valid_access_token(account_id)
        if not access_token:
            return []

        # Convert simple format to RFC3339 if needed
        t_min = time_min if "T" in time_min else f"{time_min}T00:00:00Z"
        t_max = time_max if "T" in time_max else f"{time_max}T23:59:59Z"

        url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events"
        params = {
            "timeMin": t_min,
            "timeMax": t_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "conferenceDataVersion": "1",
            "maxResults": "100"
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Google Calendar list events failed: {resp.text}")
                    return []
                data = resp.json()
                return data.get("items", [])
            except Exception as e:
                logger.error(f"Error calling Google Calendar API: {e}")
                return []

    @staticmethod
    def _to_rfc3339(dt_str: str) -> str:
        if not dt_str:
            return datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%dT%H:%M:%S+05:30")
        if "T" in dt_str and ("+" in dt_str or dt_str.endswith("Z")):
            return dt_str
        cleaned = dt_str.replace(" ", "T")
        if "+" not in cleaned and not cleaned.endswith("Z"):
            cleaned = f"{cleaned[:19]}+05:30"
        return cleaned

    @staticmethod
    async def create_calendar_event(
        event_data: dict[str, Any],
        account_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        access_token = await GoogleOAuthService.get_valid_access_token(account_id)
        if not access_token:
            logger.warning("No valid Google access token to create calendar event.")
            return None

        url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events?conferenceDataVersion=1"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        start_str = event_data.get("start_time") or event_data.get("start") or ""
        end_str = event_data.get("end_time") or event_data.get("end") or start_str
        s_iso = GoogleOAuthService._to_rfc3339(start_str)
        e_iso = GoogleOAuthService._to_rfc3339(end_str)

        body: dict[str, Any] = {
            "summary": event_data.get("title") or event_data.get("summary", "New Meeting"),
            "description": event_data.get("description", ""),
            "location": event_data.get("location", ""),
            "start": {"dateTime": s_iso, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": e_iso, "timeZone": "Asia/Kolkata"},
        }

        # Request Google Meet conference by default
        if event_data.get("add_meet", True) or event_data.get("platform") == "google_meet":
            body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"nexus_create_{int(time.time())}_{uuid.uuid4().hex[:6]}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(url, json=body, headers=headers)
                if resp.status_code not in (200, 201):
                    logger.error(f"Google Calendar create event failed ({resp.status_code}): {resp.text}")
                    return None
                data = resp.json()
                logger.info(f"Successfully created Google Calendar event on Google Cloud: {data.get('id')}")
                return data
            except Exception as e:
                logger.error(f"Error calling Google Calendar create event API: {e}")
                return None

    @staticmethod
    async def update_calendar_event(
        provider_event_id: str,
        updates: dict[str, Any],
        account_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        access_token = await GoogleOAuthService.get_valid_access_token(account_id)
        if not access_token:
            logger.warning("No valid Google access token to update calendar event.")
            return None

        clean_id = provider_event_id
        if clean_id.startswith("gcal_"):
            clean_id = clean_id[5:]

        url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events/{clean_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        patch_body: dict[str, Any] = {}
        if "title" in updates or "summary" in updates:
            patch_body["summary"] = updates.get("title") or updates.get("summary")
        if "description" in updates:
            patch_body["description"] = updates["description"]
        if "location" in updates:
            patch_body["location"] = updates["location"]

        if "start_time" in updates or "start" in updates:
            s_val = updates.get("start_time") or updates.get("start")
            s_iso = GoogleOAuthService._to_rfc3339(s_val)
            patch_body["start"] = {"dateTime": s_iso, "timeZone": "Asia/Kolkata"}

        if "end_time" in updates or "end" in updates:
            e_val = updates.get("end_time") or updates.get("end")
            e_iso = GoogleOAuthService._to_rfc3339(e_val)
            patch_body["end"] = {"dateTime": e_iso, "timeZone": "Asia/Kolkata"}
        elif ("start_time" in updates or "start" in updates) and ("end_time" not in updates and "end" not in updates):
            # Calculate default 30-min end
            s_val = updates.get("start_time") or updates.get("start")
            try:
                dt_s = datetime.strptime(s_val[:19], "%Y-%m-%d %H:%M:%S")
                dt_e = dt_s + timedelta(minutes=30)
                e_iso = dt_e.strftime("%Y-%m-%dT%H:%M:%S+05:30")
                patch_body["end"] = {"dateTime": e_iso, "timeZone": "Asia/Kolkata"}
            except Exception:
                pass

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.patch(url, json=patch_body, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Google Calendar patch event failed ({resp.status_code}): {resp.text}")
                    return None
                data = resp.json()
                logger.info(f"Successfully updated Google Calendar event {clean_id} on Google Cloud: {data.get('summary')}")
                return data
            except Exception as e:
                logger.error(f"Error calling Google Calendar patch event API: {e}")
                return None

    @staticmethod
    async def delete_calendar_event(
        provider_event_id: str,
        account_id: Optional[str] = None
    ) -> bool:
        access_token = await GoogleOAuthService.get_valid_access_token(account_id)
        if not access_token:
            return False

        clean_id = provider_event_id[5:] if provider_event_id.startswith("gcal_") else provider_event_id
        url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events/{clean_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.delete(url, headers=headers)
                return resp.status_code in (200, 204)
            except Exception as e:
                logger.error(f"Error calling Google Calendar delete event API: {e}")
                return False

    @staticmethod
    async def fetch_gmail_messages(query: str = "meeting OR invite OR scheduled", max_results: int = 20) -> list[dict[str, Any]]:
        access_token = await GoogleOAuthService.get_valid_access_token()
        if not access_token:
            return []

        url = f"{GOOGLE_GMAIL_API_BASE}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"q": query, "maxResults": str(max_results)}

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Gmail search failed: {resp.text}")
                    return []
                data = resp.json()
                msg_ids = [m["id"] for m in data.get("messages", [])]
                
                results = []
                for mid in msg_ids[:max_results]:
                    m_resp = await client.get(f"{GOOGLE_GMAIL_API_BASE}/messages/{mid}?format=metadata", headers=headers)
                    if m_resp.status_code == 200:
                        m_data = m_resp.json()
                        headers_dict = {h["name"].lower(): h["value"] for h in m_data.get("payload", {}).get("headers", [])}
                        results.append({
                            "id": mid,
                            "thread_id": m_data.get("threadId"),
                            "snippet": m_data.get("snippet", ""),
                            "subject": headers_dict.get("subject", "(No Subject)"),
                            "from": headers_dict.get("from", ""),
                            "date": headers_dict.get("date", ""),
                            "is_unread": "UNREAD" in m_data.get("labelIds", []),
                            "is_important": "IMPORTANT" in m_data.get("labelIds", [])
                        })
                return results
            except Exception as e:
                logger.error(f"Error calling Gmail API: {e}")
                return []
