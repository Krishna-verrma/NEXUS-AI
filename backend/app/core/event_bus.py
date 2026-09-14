import asyncio
from typing import Callable, Any
from collections import defaultdict

class EventBus:
    """Async event bus for distributing task and agent events to subscribers (WebSockets)."""
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[task_id].append(queue)
        return queue

    async def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            if task_id in self._subscribers and queue in self._subscribers[task_id]:
                self._subscribers[task_id].remove(queue)
                if not self._subscribers[task_id]:
                    del self._subscribers[task_id]

    async def publish(self, task_id: str, event_data: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(task_id, []))
        for q in queues:
            await q.put(event_data)

event_bus = EventBus()
