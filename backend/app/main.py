import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import init_db

# Import routers
from app.api.routes import chat, agents, tasks, files, automations, system, ws

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    try:
        init_db()
        print("[Nexus AI] Database tables verified & initialized.")
    except Exception as e:
        print(f"[Nexus AI] Database init warning: {e}")
    yield
    # Shutdown logic if any
    print("[Nexus AI] Application shutting down cleanly.")

app = FastAPI(
    title="Nexus AI Backend API",
    description="Modular intelligent operating layer with multi-agent orchestration and desktop integration.",
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(tasks.router)
app.include_router(files.router)
app.include_router(automations.router)
app.include_router(system.router)
app.include_router(ws.router)

@app.get("/")
def root():
    return {
        "service": "Nexus AI",
        "status": "operational",
        "version": settings.VERSION,
        "demoMode": settings.DEMO_MODE,
        "docsUrl": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
