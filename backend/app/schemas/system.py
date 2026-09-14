from pydantic import BaseModel
from typing import Optional

class SystemVitalsResponse(BaseModel):
    cpuUsagePercent: float
    memoryUsagePercent: float
    diskFreeGb: float
    uptimeSeconds: float
    isDemoMode: bool
    activeAgentsCount: int
    activeTasksCount: int
    backendVersion: str

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    demo_mode: Optional[bool] = None
    auto_approve_safe_actions: Optional[bool] = None
