from fastapi import APIRouter, HTTPException
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.services.chat_service import ChatService
from app.services.task_service import TaskService
from app.core.ai_client import ai_client

router = APIRouter(prefix="/api/ai", tags=["ai"])

class AiChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    task_id: Optional[str] = None
    activeTaskId: Optional[str] = None
    conversationId: Optional[str] = None
    mode: Optional[str] = "live"

class AiTaskRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    file_ids: list[str] = Field(default_factory=list)
    is_demo: bool = False

class AiTestConnectionRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None

@router.post("/chat")
async def ai_chat_endpoint(req: AiChatRequest):
    active_id = req.activeTaskId or req.task_id
    res = await ChatService.process_chat_message(
        message=req.message,
        task_id=active_id,
        active_task_id=active_id,
        conversation_id=req.conversationId,
        mode=req.mode or "live"
    )
    return res

@router.post("/task")
async def ai_task_create_endpoint(req: AiTaskRequest):
    task = await TaskService.create_and_run_task(
        prompt=req.prompt,
        file_ids=req.file_ids,
        is_demo=req.is_demo
    )
    return task

@router.get("/task/{task_id}")
def ai_task_get_endpoint(task_id: str):
    task = TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/test-connection")
async def ai_test_connection_endpoint(req: Optional[AiTestConnectionRequest] = None):
    p = req.provider if req else None
    k = req.api_key if req else None
    b = req.base_url if req else None
    m = req.model if req else None
    return await ai_client.test_connection(provider=p, api_key=k, base_url=b, model=m)
