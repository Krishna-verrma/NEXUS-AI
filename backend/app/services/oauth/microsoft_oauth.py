import os
import time
import json
import logging
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import httpx

from app.core.config import settings
from app.database.repository import Repository

logger = logging.getLogger("nexus.oauth.microsoft")

MS_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MS_GRAPH_BASE = "https://graph.microsoft.com/v1.0"

MS_SCOPES = [
    "offline_access",
    "User.Read",
    "Calendars.Read",
    "Calendars.ReadWrite",
    "Mail.Read",
    "OnlineMeetings.Read"
]

class MicrosoftOAuthService:
    @staticmethod
    def get_credentials() -> dict[str, str]:
        db_settings = Repository.get_all_settings()
        client_id = db_settings.get("microsoft_client_id") or os.getenv("MICROSOFT_CLIENT_ID", "")
        client_secret = db_settings.get("microsoft_client_secret") or os.getenv("MICROSOFT_CLIENT_SECRET", "")
        redirect_uri = db_settings.get("microsoft_redirect_uri") or os.getenv(
            "MICROSOFT_REDIRECT_URI", f"http://{settings.host}:{settings.port}/api/auth/microsoft/callback"
        )
        return {
            "client_id": client_id.strip(),
            "client_secret": client_secret.strip(),
            "redirect_uri": redirect_uri.strip()
        }

    @staticmethod
    def set_credentials(client_id: str, client_secret: str, redirect_uri: Optional[str] = None) -> None:
        Repository.set_setting("microsoft_client_id", client_id.strip())
        Repository.set_setting("microsoft_client_secret", client_secret.strip())
        if redirect_uri:
            Repository.set_setting("microsoft_redirect_uri", redirect_uri.strip())

    @staticmethod
    def generate_auth_url(redirect_uri: Optional[str] = None) -> dict[str, str]:
        creds = MicrosoftOAuthService.get_credentials()
        if not creds["client_id"]:
            raise ValueError("Microsoft Client ID is not configured. Please enter it in Settings.")

        r_uri = redirect_uri or creds["redirect_uri"]
        params = {
            "client_id": creds["client_id"],
            "redirect_uri": r_uri,
            "response_type": "code",
            "scope": " ".join(MS_SCOPES),
            "response_mode": "query",
            "state": f"nexus_ms_{int(time.time())}"
        }
        url = f"{MS_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return {"auth_url": url, "state": params["state"]}

    @staticmethod
    async def exchange_code_for_tokens(code: str, redirect_uri: Optional[str] = None) -> dict[str, Any]:
        creds = MicrosoftOAuthService.get_credentials()
        if not creds["client_id"] or not creds["client_secret"]:
            raise ValueError("Microsoft Client ID and Secret must be configured.")

        r_uri = redirect_uri or creds["redirect_uri"]
        payload = {
            "code": code,
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "redirect_uri": r_uri,
            "grant_type": "authorization_code",
            "scope": " ".join(MS_SCOPES)
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(MS_TOKEN_URL, data=payload)
            if resp.status_code != 200:
                logger.error(f"Microsoft token exchange failed: {resp.text}")
                raise RuntimeError(f"Failed to exchange Microsoft OAuth code: {resp.text}")
            token_data = resp.json()

            # Retrieve user profile
            me_resp = await client.get(
                f"{MS_GRAPH_BASE}/me",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_email = "user@outlook.com"
            user_name = "Microsoft User"
            if me_resp.status_code == 200:
                me_info = me_resp.json()
                user_email = me_info.get("mail") or me_info.get("userPrincipalName", user_email)
                user_name = me_info.get("displayName", user_name)

            account_id = f"microsoft_{user_email.replace('@', '_').replace('.', '_')}"
            expires_in = token_data.get("expires_in", 3600)
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).strftime("%Y-%m-%d %H:%M:%S")

            Repository.save_connected_account(
                account_id=account_id,
                provider="microsoft",
                account_email=user_email,
                account_name=user_name,
                status="connected",
                scopes=MS_SCOPES
            )
            Repository.save_oauth_tokens(
                account_id=account_id,
                provider="microsoft",
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
            account = Repository.get_connected_account_by_provider("microsoft")

        if not account:
            return None

        tokens = Repository.get_oauth_tokens(account["id"])
        if not tokens or not tokens.get("access_token"):
            return None

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

        refresh_tok = tokens.get("refresh_token")
        if not refresh_tok:
            logger.warning(f"Microsoft token for {account['account_email']} is expired and has no refresh token.")
            Repository.save_connected_account(account["id"], "microsoft", account["account_email"], status="needs_reauth")
            return None

        creds = MicrosoftOAuthService.get_credentials()
        payload = {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": refresh_tok,
            "grant_type": "refresh_token",
            "scope": " ".join(MS_SCOPES)
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(MS_TOKEN_URL, data=payload)
            if resp.status_code == 200:
                new_data = resp.json()
                new_access = new_data["access_token"]
                expires_in = new_data.get("expires_in", 3600)
                new_exp = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).strftime("%Y-%m-%d %H:%M:%S")
                Repository.save_oauth_tokens(
                    account_id=account["id"],
                    provider="microsoft",
                    access_token=new_access,
                    refresh_token=new_data.get("refresh_token") or refresh_tok,
                    expires_at=new_exp
                )
                Repository.save_connected_account(account["id"], "microsoft", account["account_email"], status="connected")
                return new_access
            else:
                logger.error(f"Failed to refresh Microsoft token: {resp.text}")
                Repository.save_connected_account(account["id"], "microsoft", account["account_email"], status="needs_reauth")
                return None

    @staticmethod
    async def fetch_calendar_events(
        start_datetime: str,
        end_datetime: str,
        account_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        access_token = await MicrosoftOAuthService.get_valid_access_token(account_id)
        if not access_token:
            return []

        # Microsoft calendarView expects ISO 8601 strings
        s_dt = start_datetime.replace(" ", "T")
        if not s_dt.endswith("Z") and "+" not in s_dt:
            s_dt += "Z"
        e_dt = end_datetime.replace(" ", "T")
        if not e_dt.endswith("Z") and "+" not in e_dt:
            e_dt += "Z"

        url = f"{MS_GRAPH_BASE}/me/calendarView"
        params = {
            "startDateTime": s_dt,
            "endDateTime": e_dt,
            "$top": "100",
            "$select": "id,subject,bodyPreview,start,end,location,attendees,organizer,isCancelled,isOnlineMeeting,onlineMeetingProvider,onlineMeetingUrl,onlineMeeting"
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Prefer": 'outlook.timezone="Asia/Kolkata"'
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Microsoft Calendar list failed: {resp.text}")
                    return []
                data = resp.json()
                return data.get("value", [])
            except Exception as e:
                logger.error(f"Error calling Microsoft Graph calendarView: {e}")
                return []

    @staticmethod
    async def create_calendar_event(
        event_data: dict[str, Any],
        account_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        access_token = await MicrosoftOAuthService.get_valid_access_token(account_id)
        if not access_token:
            return None

        url = f"{MS_GRAPH_BASE}/me/events"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": 'outlook.timezone="Asia/Kolkata"'
        }

        start_str = event_data.get("start_time") or event_data.get("start") or ""
        end_str = event_data.get("end_time") or event_data.get("end") or start_str
        s_clean = start_str[:19].replace(" ", "T")
        e_clean = end_str[:19].replace(" ", "T")

        body = {
            "subject": event_data.get("title") or event_data.get("summary", "New Meeting"),
            "body": {"contentType": "HTML", "content": event_data.get("description", "")},
            "start": {"dateTime": s_clean, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": e_clean, "timeZone": "Asia/Kolkata"},
            "location": {"displayName": event_data.get("location", "")},
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(url, json=body, headers=headers)
                if resp.status_code not in (200, 201):
                    logger.error(f"Microsoft create event failed: {resp.text}")
                    return None
                return resp.json()
            except Exception as e:
                logger.error(f"Error calling Microsoft create event API: {e}")
                return None

    @staticmethod
    async def update_calendar_event(
        provider_event_id: str,
        updates: dict[str, Any],
        account_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        access_token = await MicrosoftOAuthService.get_valid_access_token(account_id)
        if not access_token:
            return None

        clean_id = provider_event_id[3:] if provider_event_id.startswith("ms_") else provider_event_id
        url = f"{MS_GRAPH_BASE}/me/events/{clean_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": 'outlook.timezone="Asia/Kolkata"'
        }

        patch_body: dict[str, Any] = {}
        if "title" in updates or "subject" in updates:
            patch_body["subject"] = updates.get("title") or updates.get("subject")
        if "location" in updates:
            patch_body["location"] = {"displayName": updates["location"]}
        if "description" in updates:
            patch_body["body"] = {"contentType": "HTML", "content": updates["description"]}
        if "start_time" in updates or "start" in updates:
            s_val = updates.get("start_time") or updates.get("start")
            patch_body["start"] = {"dateTime": s_val[:19].replace(" ", "T"), "timeZone": "Asia/Kolkata"}
        if "end_time" in updates or "end" in updates:
            e_val = updates.get("end_time") or updates.get("end")
            patch_body["end"] = {"dateTime": e_val[:19].replace(" ", "T"), "timeZone": "Asia/Kolkata"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.patch(url, json=patch_body, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Microsoft patch event failed: {resp.text}")
                    return None
                return resp.json()
            except Exception as e:
                logger.error(f"Error calling Microsoft patch event API: {e}")
                return None

    @staticmethod
    async def delete_calendar_event(
        provider_event_id: str,
        account_id: Optional[str] = None
    ) -> bool:
        access_token = await MicrosoftOAuthService.get_valid_access_token(account_id)
        if not access_token:
            return False

        clean_id = provider_event_id[3:] if provider_event_id.startswith("ms_") else provider_event_id
        url = f"{MS_GRAPH_BASE}/me/events/{clean_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.delete(url, headers=headers)
                return resp.status_code in (200, 204)
            except Exception as e:
                logger.error(f"Error calling Microsoft delete event API: {e}")
                return False

    @staticmethod
    async def fetch_outlook_messages(query: Optional[str] = None, max_results: int = 25) -> list[dict[str, Any]]:
        access_token = await MicrosoftOAuthService.get_valid_access_token()
        if not access_token:
            return []

        url = f"{MS_GRAPH_BASE}/me/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        params: dict[str, str] = {
            "$top": str(max_results),
            "$orderby": "receivedDateTime desc",
            "$select": "id,conversationId,subject,bodyPreview,from,receivedDateTime,isRead,importance"
        }
        if query:
            params["$search"] = f'"{query}"'

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Outlook messages fetch failed: {resp.text}")
                    return []
                data = resp.json()
                items = data.get("value", [])
                results = []
                for item in items:
                    results.append({
                        "id": item["id"],
                        "thread_id": item.get("conversationId"),
                        "subject": item.get("subject", "(No Subject)"),
                        "snippet": item.get("bodyPreview", ""),
                        "from": item.get("from", {}).get("emailAddress", {}).get("name", ""),
                        "sender_email": item.get("from", {}).get("emailAddress", {}).get("address", ""),
                        "received_at": item.get("receivedDateTime"),
                        "is_read": item.get("isRead", False),
                        "is_important": item.get("importance") == "high"
                    })
                return results
            except Exception as e:
                logger.error(f"Error calling Microsoft Graph messages: {e}")
                return []
