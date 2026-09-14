from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel
from app.models.schemas import SettingsDTO, SettingsUpdateRequest
from app.core.config import settings
from app.core.security import mask_api_key
from app.core.ai_client import ai_client
from app.database.repository import Repository

from app.services.calendar_service import CalendarService
from app.services.github_service import GitHubService

class TestAiRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None

class TestGithubRequest(BaseModel):
    token: Optional[str] = None

class SyncGithubRequest(BaseModel):
    token: Optional[str] = None
    repo: Optional[str] = None

router = APIRouter(prefix="/api", tags=["settings"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "demo_mode": settings.demo_mode
    }

@router.get("/settings", response_model=SettingsDTO)
def get_settings():
    # Sync from DB if present
    db_settings = Repository.get_all_settings()
    provider = db_settings.get("ai_provider", settings.ai_provider)
    api_key = db_settings.get("ai_api_key", settings.ai_api_key)
    base_url = db_settings.get("ai_base_url", settings.ai_base_url)
    model = db_settings.get("ai_model", settings.ai_model)
    temp = float(db_settings.get("ai_temperature", settings.ai_temperature))
    max_tokens = int(db_settings.get("ai_max_tokens", settings.ai_max_tokens))
    demo = db_settings.get("demo_mode", str(settings.demo_mode)).lower() in ("true", "1")
    web_search = db_settings.get("enable_web_search", str(settings.enable_web_search)).lower() in ("true", "1")
    google_cal = db_settings.get("google_calendar_url", "")
    outlook_cal = db_settings.get("outlook_calendar_url", "")
    auto_scan = db_settings.get("auto_scan_pc", "true").lower() in ("true", "1")
    web_search_key = db_settings.get("web_search_api_key", "")
    gh_token = db_settings.get("github_token", settings.github_token or "")
    gh_repo = db_settings.get("github_repo", settings.github_repo or "")

    return SettingsDTO(
        ai_provider=provider,
        ai_api_key=mask_api_key(api_key),
        ai_base_url=base_url,
        ai_model=model,
        ai_temperature=temp,
        ai_max_tokens=max_tokens,
        demo_mode=demo,
        enable_web_search=web_search,
        google_calendar_url=google_cal or None,
        outlook_calendar_url=outlook_cal or None,
        auto_scan_pc=auto_scan,
        web_search_api_key=mask_api_key(web_search_key) if web_search_key else None,
        github_token=mask_api_key(gh_token) if gh_token else None,
        github_repo=gh_repo or None,
        is_configured=bool(api_key and not demo)
    )

@router.post("/settings", response_model=SettingsDTO)
def update_settings(req: SettingsUpdateRequest):
    db_settings = Repository.get_all_settings()
    current_key = db_settings.get("ai_api_key", settings.ai_api_key)

    new_key = current_key
    if req.ai_api_key is not None and not req.ai_api_key.startswith("***"):
        new_key = req.ai_api_key
        Repository.set_setting("ai_api_key", new_key)

    if req.ai_provider is not None:
        settings.ai_provider = req.ai_provider
        Repository.set_setting("ai_provider", req.ai_provider)
    if req.ai_base_url is not None:
        settings.ai_base_url = req.ai_base_url
        Repository.set_setting("ai_base_url", req.ai_base_url)
    if req.ai_model is not None:
        settings.ai_model = req.ai_model
        Repository.set_setting("ai_model", req.ai_model)
    if req.ai_temperature is not None:
        settings.ai_temperature = req.ai_temperature
        Repository.set_setting("ai_temperature", str(req.ai_temperature))
    if req.ai_max_tokens is not None:
        settings.ai_max_tokens = req.ai_max_tokens
        Repository.set_setting("ai_max_tokens", str(req.ai_max_tokens))
    if req.demo_mode is not None:
        settings.demo_mode = req.demo_mode
        Repository.set_setting("demo_mode", "true" if req.demo_mode else "false")
    elif new_key and new_key.strip():
        # If user saves a new API key without explicitly keeping demo mode, switch to live mode
        settings.demo_mode = False
        Repository.set_setting("demo_mode", "false")

    if req.enable_web_search is not None:
        settings.enable_web_search = req.enable_web_search
        Repository.set_setting("enable_web_search", "true" if req.enable_web_search else "false")

    if req.google_calendar_url is not None:
        Repository.set_setting("google_calendar_url", req.google_calendar_url)
        if req.google_calendar_url.strip():
            try:
                CalendarService.sync_ics_url(req.google_calendar_url.strip(), source_name="google_calendar")
            except Exception:
                pass

    if req.outlook_calendar_url is not None:
        Repository.set_setting("outlook_calendar_url", req.outlook_calendar_url)
        if req.outlook_calendar_url.strip():
            try:
                CalendarService.sync_ics_url(req.outlook_calendar_url.strip(), source_name="outlook")
            except Exception:
                pass

    if req.auto_scan_pc is not None:
        Repository.set_setting("auto_scan_pc", "true" if req.auto_scan_pc else "false")

    if req.web_search_api_key is not None and not req.web_search_api_key.startswith("***"):
        Repository.set_setting("web_search_api_key", req.web_search_api_key)

    if req.github_token is not None and not req.github_token.startswith("***"):
        Repository.set_setting("github_token", req.github_token)

    if req.github_repo is not None:
        Repository.set_setting("github_repo", req.github_repo)

    ai_client.update_config(
        provider=settings.ai_provider,
        api_key=new_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        temperature=settings.ai_temperature,
        max_tokens=settings.ai_max_tokens,
        demo_mode=settings.demo_mode
    )

    return get_settings()

@router.post("/settings/test-ai")
async def test_ai_connection(req: Optional[TestAiRequest] = None):
    p = req.provider if req else None
    k = req.api_key if req else None
    b = req.base_url if req else None
    m = req.model if req else None
    return await ai_client.test_connection(provider=p, api_key=k, base_url=b, model=m)

@router.post("/settings/test-github")
async def test_github_connection(req: TestGithubRequest):
    token = req.token
    if not token or token.startswith("***"):
        db_settings = Repository.get_all_settings()
        token = db_settings.get("github_token", "")
    return await GitHubService.test_connection(token or "")

@router.post("/settings/sync-github")
async def sync_github(req: SyncGithubRequest):
    token = req.token
    if not token or token.startswith("***"):
        db_settings = Repository.get_all_settings()
        token = db_settings.get("github_token", "")
    repo = req.repo
    if not repo:
        db_settings = Repository.get_all_settings()
        repo = db_settings.get("github_repo", "")
    return await GitHubService.sync_github_deliverables(token=token, repo=repo)


