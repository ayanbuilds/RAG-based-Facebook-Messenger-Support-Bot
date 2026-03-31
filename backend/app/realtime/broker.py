import asyncio
from typing import Dict, Set, Any

class EventBroker:
    def __init__(self) -> None:
        self._subs: Dict[int, Set[asyncio.Queue]] = {}  # conversation_id -> set(queues)
        self._lock = asyncio.Lock()

    async def subscribe(self, conversation_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subs.setdefault(conversation_id, set()).add(q)
        return q

    async def unsubscribe(self, conversation_id: int, q: asyncio.Queue) -> None:
        async with self._lock:
            if conversation_id in self._subs and q in self._subs[conversation_id]:
                self._subs[conversation_id].remove(q)
                if not self._subs[conversation_id]:
                    self._subs.pop(conversation_id, None)

    async def publish(self, conversation_id: int, payload: Any) -> None:
        async with self._lock:
            queues = list(self._subs.get(conversation_id, set()))
        for q in queues:
            await q.put(payload)

broker = EventBroker()
