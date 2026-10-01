import asyncio
from typing import Dict, Set, Any
from app.core.logging import logger

class EventBus:
    def __init__(self):
        # task_id (str) -> Set[asyncio.Queue]
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        async with self._lock:
            if task_id not in self._subscribers:
                self._subscribers[task_id] = set()
            queue: asyncio.Queue = asyncio.Queue()
            self._subscribers[task_id].add(queue)
            return queue

    async def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        async with self._lock:
            if task_id in self._subscribers:
                self._subscribers[task_id].discard(queue)
                if not self._subscribers[task_id]:
                    del self._subscribers[task_id]

    async def publish(self, task_id: str, event_data: Dict[str, Any]):
        async with self._lock:
            queues = list(self._subscribers.get(task_id, set()))
        for q in queues:
            try:
                q.put_nowait(event_data)
            except Exception as e:
                logger.warning(f"Failed to put event in queue for task {task_id}: {e}")

event_bus = EventBus()
