import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.event_bus import event_bus

logger = logging.getLogger("nexus.websocket")
router = APIRouter(tags=["websocket"])

@router.websocket("/ws/tasks/{task_id}")
async def task_websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    queue = await event_bus.subscribe(task_id)
    try:
        # Send initial confirmation
        await websocket.send_json({
            "type": "connected",
            "task_id": task_id,
            "message": "Connected to real-time agent stream."
        })
        while True:
            event_data = await queue.get()
            await websocket.send_json(event_data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        await event_bus.unsubscribe(task_id, queue)
