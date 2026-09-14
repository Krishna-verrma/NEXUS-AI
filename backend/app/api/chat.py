from fastapi import APIRouter
from typing import Optional
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("", response_model=ChatMessageResponse)
async def post_chat_message(req: ChatMessageRequest):
    active_id = req.activeTaskId or req.task_id
    res = await ChatService.process_chat_message(
        message=req.message,
        task_id=active_id,
        active_task_id=active_id,
        conversation_id=req.conversationId,
        mode=req.mode or "live"
    )
    return res

@router.get("/messages")
def get_chat_messages(task_id: Optional[str] = None):
    return ChatService.get_messages(task_id=task_id)
