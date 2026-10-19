import asyncio
from typing import Protocol

class Store(Protocol):
    async def load(self, session_id: str) -> str: ...

class MemoryView:
    def __init__(self, store: Store):
        self.store = store
        self._cache: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> str:
        async with self._lock:
            if session_id in self._cache:
                return self._cache[session_id]
        value = await self.store.load(session_id)
        async with self._lock:
            self._cache[session_id] = value
        return value

    async def invalidate(self, session_id: str) -> None:
        async with self._lock:
            self._cache.pop(session_id, None)
