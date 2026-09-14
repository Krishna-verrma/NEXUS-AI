import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import ws_manager
from app.agents import orchestrator

router = APIRouter(tags=["WebSocket"])

@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Send initial welcome & connection confirmation
    await websocket.send_json({
        "type": "connection_established",
        "message": "Connected to Nexus AI Real-Time Agent Stream",
        "activeAgents": 9,
        "protocol": "nexus-v1"
    })

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
                action = msg.get("action")

                if action == "ping":
                    await websocket.send_json({"type": "pong"})

                elif action == "chat":
                    user_prompt = msg.get("message", "")
                    session_id = msg.get("sessionId", "default")
                    
                    # Stream tokens callback
                    async def stream_callback(trace):
                        await ws_manager.emit_agent_trace(trace)

                    # Execute and stream result
                    res = orchestrator.execute(user_prompt)
                    
                    # Emit final completion
                    await websocket.send_json({
                        "type": "chat_response",
                        "sessionId": session_id,
                        "data": res.to_dict()
                    })

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON format"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
