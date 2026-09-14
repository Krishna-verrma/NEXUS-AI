from typing import List, Dict, Any
import json
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    async def emit_agent_trace(self, trace: Dict[str, Any]):
        await self.broadcast_json({
            "type": "agent_trace",
            "data": trace
        })

    async def emit_token_chunk(self, chunk: str, session_id: str):
        await self.broadcast_json({
            "type": "token_chunk",
            "sessionId": session_id,
            "chunk": chunk
        })

    async def emit_security_ticket(self, ticket: Dict[str, Any]):
        await self.broadcast_json({
            "type": "security_ticket",
            "data": ticket
        })

    async def emit_task_update(self, task_data: Dict[str, Any]):
        await self.broadcast_json({
            "type": "task_update",
            "data": task_data
        })

ws_manager = WebSocketManager()
