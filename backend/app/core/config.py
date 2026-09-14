import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "nexus_ai.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "NEXUS AI"
    version: str = "1.0.0"
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    ai_api_key: Optional[str] = os.getenv("AI_API_KEY", "")
    ai_base_url: str = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    ai_model: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    ai_max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "2048"))
    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    enable_web_search: bool = os.getenv("ENABLE_WEB_SEARCH", "false").lower() in ("true", "1", "yes")
    github_token: Optional[str] = os.getenv("GITHUB_TOKEN", "")
    github_repo: Optional[str] = os.getenv("GITHUB_REPO", "")
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "127.0.0.1")
    max_file_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    allowed_extensions: list[str] = ["csv", "xlsx", "json", "pdf", "docx", "txt", "py", "cpp", "java", "js", "ts", "sql", "md"]

settings = Settings()
