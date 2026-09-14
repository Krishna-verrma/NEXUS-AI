import logging
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.database.repository import Repository
from app.services.oauth.google_oauth import GoogleOAuthService
from app.services.oauth.microsoft_oauth import MicrosoftOAuthService
from app.integrations.calendar.unified_calendar import UnifiedCalendarEngine

logger = logging.getLogger("nexus.api.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

class OAuthConfigRequest(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None

@router.get("/status")
async def get_connection_status():
    """
    Returns live connection status for:
    Google, Google Calendar, Gmail, Google Meet,
    Microsoft, Outlook Mail, Outlook Calendar, Teams.
    """
    g_acc = Repository.get_connected_account_by_provider("google")
    g_tokens = Repository.get_oauth_tokens_by_provider("google") if g_acc else None
    google_connected = bool(g_acc and g_acc.get("status") == "connected" and g_tokens and g_tokens.get("access_token"))

    ms_acc = Repository.get_connected_account_by_provider("microsoft")
    ms_tokens = Repository.get_oauth_tokens_by_provider("microsoft") if ms_acc else None
    ms_connected = bool(ms_acc and ms_acc.get("status") == "connected" and ms_tokens and ms_tokens.get("access_token"))

    # Also check if private calendar URLs or local integration are configured
    db_settings = Repository.get_all_settings()
    has_gcal_url = bool(db_settings.get("google_calendar_url"))
    has_outlook_url = bool(db_settings.get("outlook_calendar_url"))

    def extract_email_from_ical(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        import re, urllib.parse
        m = re.search(r"/ical/([^/]+)/", url)
        if m:
            return urllib.parse.unquote(m.group(1))
        return None

    gcal_email = extract_email_from_ical(db_settings.get("google_calendar_url"))
    last_sync = Repository.get_sync_state("last_calendar_sync") or "Not synced yet"

    g_creds = GoogleOAuthService.get_credentials()
    ms_creds = MicrosoftOAuthService.get_credentials()

    return {
        "google": {
            "name": "Google",
            "connected": google_connected or has_gcal_url,
            "account_email": g_acc.get("account_email") if g_acc else (gcal_email or ("iCal Calendar Feed" if has_gcal_url else None)),
            "status": "Connected" if (google_connected or has_gcal_url) else "Not Connected",
            "type": "OAuth 2.0" if google_connected else ("Web Feed" if has_gcal_url else "None"),
            "client_id": g_creds.get("client_id", ""),
            "has_secret": bool(g_creds.get("client_secret")),
            "redirect_uri": g_creds.get("redirect_uri", "")
        },
        "google_calendar": {
            "name": "Google Calendar",
            "connected": google_connected or has_gcal_url,
            "status": "Connected" if (google_connected or has_gcal_url) else "Not Connected"
        },
        "gmail": {
            "name": "Gmail",
            "connected": google_connected,
            "account_email": g_acc.get("account_email") if g_acc else None,
            "status": "Connected" if google_connected else "Not Connected",
            "client_id": g_creds.get("client_id", ""),
            "has_secret": bool(g_creds.get("client_secret")),
            "redirect_uri": g_creds.get("redirect_uri", "")
        },
        "google_meet": {
            "name": "Google Meet",
            "connected": google_connected or has_gcal_url,
            "status": "Connected" if (google_connected or has_gcal_url) else "Not Connected"
        },
        "microsoft": {
            "name": "Microsoft",
            "connected": ms_connected or has_outlook_url,
            "account_email": ms_acc.get("account_email") if ms_acc else (
                "24ff430eb7ae47169d41c31e3135a3f7@cuchd.in" if has_outlook_url else None
            ),
            "status": "Connected" if (ms_connected or has_outlook_url) else "Not Connected",
            "type": "Microsoft Graph OAuth" if ms_connected else ("Web Feed" if has_outlook_url else "None"),
            "client_id": ms_creds.get("client_id", ""),
            "has_secret": bool(ms_creds.get("client_secret")),
            "redirect_uri": ms_creds.get("redirect_uri", "")
        },
        "outlook_mail": {
            "name": "Outlook Mail",
            "connected": ms_connected,
            "status": "Connected" if ms_connected else "Not Connected"
        },
        "outlook_calendar": {
            "name": "Outlook Calendar",
            "connected": ms_connected or has_outlook_url,
            "status": "Connected" if (ms_connected or has_outlook_url) else "Not Connected"
        },
        "teams": {
            "name": "Teams",
            "connected": ms_connected or has_outlook_url,
            "status": "Connected / Available" if (ms_connected or has_outlook_url) else "Not Connected"
        },
        "last_synced_at": last_sync
    }

# ── Google OAuth Endpoints ──

@router.get("/google/login")
@router.get("/login/google")
def google_login(redirect_uri: Optional[str] = None, direct: bool = False):
    try:
        data = GoogleOAuthService.generate_auth_url(redirect_uri)
        if direct:
            return RedirectResponse(url=data["auth_url"])
        return {"url": data["auth_url"], "auth_url": data["auth_url"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/google/callback")
@router.get("/callback/google")
async def google_callback(code: str, state: Optional[str] = None, error: Optional[str] = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth authorization error: {error}")
    try:
        res = await GoogleOAuthService.exchange_code_for_tokens(code)
        # Trigger background calendar sync
        try:
            await UnifiedCalendarEngine.sync_all_calendars()
        except Exception:
            pass
        # Redirect back to frontend dashboard/settings
        return RedirectResponse(url="/#settings?auth=google_success")
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return RedirectResponse(url=f"/#settings?auth_error={str(e)}")

@router.get("/google/config")
@router.get("/config/google")
def get_google_config():
    creds = GoogleOAuthService.get_credentials()
    return {
        "client_id": creds.get("client_id", ""),
        "has_secret": bool(creds.get("client_secret")),
        "redirect_uri": creds.get("redirect_uri", "")
    }

@router.post("/google/config")
@router.post("/config/google")
def set_google_config(req: OAuthConfigRequest):
    GoogleOAuthService.set_credentials(req.client_id, req.client_secret, req.redirect_uri)
    return {"success": True, "message": "Google OAuth credentials updated."}

@router.post("/google/disconnect")
@router.post("/disconnect/google")
def disconnect_google():
    Repository.delete_connected_accounts_by_provider("google")
    return {"success": True, "message": "Google account disconnected."}

@router.get("/google/test-gmail")
@router.post("/google/test-gmail")
async def test_gmail_connection(query: str = "meeting OR invite OR scheduled OR project"):
    """Test retrieving messages directly via live Gmail API."""
    try:
        g_acc = Repository.get_connected_account_by_provider("google")
        if not g_acc:
            return {
                "success": False,
                "message": "Google account is not connected. Please connect via OAuth 2.0 first.",
                "count": 0,
                "messages": []
            }
        messages = await GoogleOAuthService.fetch_gmail_messages(query=query, max_results=10)
        return {
            "success": True,
            "message": f"Gmail connected! Found {len(messages)} matching communications.",
            "count": len(messages),
            "account_email": g_acc.get("account_email"),
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Error testing Gmail connection: {e}")
        return {
            "success": False,
            "message": f"Gmail query failed: {str(e)}",
            "count": 0,
            "messages": []
        }

# ── Microsoft OAuth Endpoints ──

@router.get("/microsoft/login")
@router.get("/login/microsoft")
def microsoft_login(redirect_uri: Optional[str] = None, direct: bool = False):
    try:
        data = MicrosoftOAuthService.generate_auth_url(redirect_uri)
        if direct:
            return RedirectResponse(url=data["auth_url"])
        return {"url": data["auth_url"], "auth_url": data["auth_url"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/microsoft/callback")
@router.get("/callback/microsoft")
async def microsoft_callback(code: str, state: Optional[str] = None, error: Optional[str] = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Microsoft OAuth error: {error}")
    try:
        res = await MicrosoftOAuthService.exchange_code_for_tokens(code)
        try:
            await UnifiedCalendarEngine.sync_all_calendars()
        except Exception:
            pass
        return RedirectResponse(url="/#settings?auth=microsoft_success")
    except Exception as e:
        logger.error(f"Microsoft OAuth callback error: {e}")
        return RedirectResponse(url=f"/#settings?auth_error={str(e)}")

@router.get("/microsoft/config")
@router.get("/config/microsoft")
def get_microsoft_config():
    creds = MicrosoftOAuthService.get_credentials()
    return {
        "client_id": creds.get("client_id", ""),
        "has_secret": bool(creds.get("client_secret")),
        "redirect_uri": creds.get("redirect_uri", "")
    }

@router.post("/microsoft/config")
@router.post("/config/microsoft")
def set_microsoft_config(req: OAuthConfigRequest):
    MicrosoftOAuthService.set_credentials(req.client_id, req.client_secret, req.redirect_uri)
    return {"success": True, "message": "Microsoft OAuth credentials updated."}

@router.post("/microsoft/disconnect")
@router.post("/disconnect/microsoft")
def disconnect_microsoft():
    Repository.delete_connected_accounts_by_provider("microsoft")
    return {"success": True, "message": "Microsoft account disconnected."}

# ── Manual / Incremental Sync Endpoint ──

@router.post("/sync")
async def trigger_sync():
    """Trigger immediate calendar and email sync."""
    res = await UnifiedCalendarEngine.sync_all_calendars()
    return res
