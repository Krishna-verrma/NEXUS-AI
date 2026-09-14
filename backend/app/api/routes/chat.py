import json
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db
from app.models.chat import ChatSessionModel, ChatMessageModel
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionResponse
from app.agents import orchestrator, get_agent
from app.services.websocket_manager import ws_manager
from app.services.security_service import register_ticket

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(payload: ChatMessageCreate, db: Session = Depends(get_db)):
    """Primary chat endpoint: dispatches through Nexus Orchestrator."""
    session_id = payload.session_id
    if not session_id:
        new_session = ChatSessionModel(title=payload.message[:30] + "...")
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id
    else:
        existing = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
        if not existing:
            new_session = ChatSessionModel(id=session_id, title=payload.message[:30] + "...")
            db.add(new_session)
            db.commit()

    # Save User message
    user_msg_id = str(uuid.uuid4())
    user_msg = ChatMessageModel(
        id=user_msg_id,
        session_id=session_id,
        sender="user",
        content=payload.message,
        status="completed",
        created_at=datetime.datetime.utcnow()
    )
    db.add(user_msg)
    db.commit()

    # Define live callback for websocket broadcasting
    def trace_callback(trace_dict):
        # We can fire and forget or run in loop
        pass

    # Execute orchestrator
    agent_target = payload.target_agent
    if agent_target and agent_target != "orchestrator":
        selected_agent = get_agent(agent_target)
        result = selected_agent.execute(payload.message, context={"target_agent": agent_target}, callback=trace_callback)
    else:
        result = orchestrator.execute(payload.message, callback=trace_callback)

    # If ticket was generated, register in security service
    ticket_id = None
    if result.security_ticket:
        ticket_id = result.security_ticket["id"]
        register_ticket(result.security_ticket)
        # Broadcast ticket to websocket
        await ws_manager.emit_security_ticket(result.security_ticket)

    # Save Assistant message
    assistant_msg_id = str(uuid.uuid4())
    assistant_msg = ChatMessageModel(
        id=assistant_msg_id,
        session_id=session_id,
        sender="assistant",
        content=result.response,
        agent_role=result.agent_role,
        status=result.status,
        activity_traces=json.dumps(result.activity_traces),
        security_ticket_id=ticket_id,
        created_at=datetime.datetime.utcnow()
    )
    db.add(assistant_msg)
    db.commit()

    return ChatMessageResponse(
        id=assistant_msg_id,
        sessionId=session_id,
        sender="assistant",
        content=result.response,
        timestamp=datetime.datetime.utcnow().isoformat(),
        agentRole=result.agent_role,
        status=result.status,
        activityTraces=result.activity_traces,
        securityTicketId=ticket_id
    )

@router.get("/sessions", response_model=list[ChatSessionResponse])
def get_chat_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSessionModel).order_by(ChatSessionModel.updated_at.desc()).all()
    out = []
    for s in sessions:
        count = db.query(ChatMessageModel).filter(ChatMessageModel.session_id == s.id).count()
        out.append(ChatSessionResponse(
            id=s.id,
            title=s.title,
            createdAt=s.created_at.isoformat() if s.created_at else "",
            updatedAt=s.updated_at.isoformat() if s.updated_at else "",
            messageCount=count
        ))
    return out

@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ChatMessageModel).filter(ChatMessageModel.session_id == session_id).order_by(ChatMessageModel.created_at.asc()).all()
    out = []
    for m in messages:
        traces = []
        if m.activity_traces:
            try:
                traces = json.loads(m.activity_traces)
            except Exception:
                traces = []
        out.append({
            "id": m.id,
            "sessionId": m.session_id,
            "sender": m.sender,
            "content": m.content,
            "timestamp": m.created_at.isoformat() if m.created_at else "",
            "agentRole": m.agent_role,
            "status": m.status,
            "activityTraces": traces,
            "securityTicketId": m.security_ticket_id
        })
    return out
