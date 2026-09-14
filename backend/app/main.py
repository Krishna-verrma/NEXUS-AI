import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.connection import init_db
from app.database.repository import Repository
from app.core.ai_client import ai_client

from app.api.tasks import router as tasks_router
from app.api.chat import router as chat_router
from app.api.agents import router as agents_router
from app.api.files import router as files_router
from app.api.reports import router as reports_router
from app.api.settings import router as settings_router
from app.api.ws import router as ws_router
from app.api.calendar import router as calendar_router
from app.api.ai_routes import router as ai_router
from app.api.auth_routes import router as auth_router
from app.services.sync_service import SyncService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nexus.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Nexus AI database and system agents...")
    init_db()
    
    # Load stored settings into memory
    db_settings = Repository.get_all_settings()
    if db_settings:
        provider = db_settings.get("ai_provider", settings.ai_provider)
        key = db_settings.get("ai_api_key", settings.ai_api_key)
        base_url = db_settings.get("ai_base_url", settings.ai_base_url)
        model = db_settings.get("ai_model", settings.ai_model)
        temp = float(db_settings.get("ai_temperature", settings.ai_temperature))
        max_tokens = int(db_settings.get("ai_max_tokens", settings.ai_max_tokens))
        demo = db_settings.get("demo_mode", str(settings.demo_mode)).lower() in ("true", "1")
        ai_client.update_config(provider, key, base_url, model, temp, max_tokens, demo)
        
    logger.info("Nexus AI backend ready.")

    # Section 10: Automatic Daily Sync & Background loop
    try:
        import asyncio
        asyncio.create_task(SyncService.run_initial_startup_sync())
        asyncio.create_task(SyncService.start_background_sync(interval_seconds=300))
    except Exception as e:
        logger.warning(f"Could not launch initial sync: {e}")

    yield
    # Shutdown
    logger.info("Nexus AI backend shutting down...")
    SyncService.stop_background_sync()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Intelligent Multi-Agent Desktop Workspace Backend",
    lifespan=lifespan
)

# CORS configuration allowing frontend from localhost (Vite: 5173, Electron: app://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred in Nexus AI.", "error": str(exc)}
    )

# Register Routers
app.include_router(settings_router)
app.include_router(tasks_router)
app.include_router(chat_router)
app.include_router(agents_router)
app.include_router(files_router)
app.include_router(reports_router)
app.include_router(ws_router)
app.include_router(calendar_router)
app.include_router(ai_router)
app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
