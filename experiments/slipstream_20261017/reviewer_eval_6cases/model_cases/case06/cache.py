import asyncio
from collections import OrderedDict
from typing import Protocol

class Repository(Protocol):
    async def search(self, tenant: str, query: str) -> tuple[str, ...]: ...

class ContextCache:
    def __init__(self, repository: Repository, tenants: set[str], capacity: int = 64):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.repository = repository
        self.capacity = capacity
        self._epoch = {tenant: 0 for tenant in tenants}
        self._values: OrderedDict[tuple[str, str], tuple[str, ...]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, tenant: str, query: str) -> tuple[str, ...]:
        key = (tenant, query)
        async with self._lock:
            epoch = self._epoch[tenant]
            if key in self._values:
                self._values.move_to_end(key)
                return self._values[key]
        result = tuple(await self.repository.search(tenant, query))
        async with self._lock:
            if self._epoch[tenant] == epoch:
                self._values[key] = result
                self._values.move_to_end(key)
                while len(self._values) > self.capacity:
                    self._values.popitem(last=False)
        return result

    async def invalidate(self, tenant: str) -> None:
        async with self._lock:
            self._epoch[tenant] += 1
            for key in list(self._values):
                if key[0] == tenant:
                    del self._values[key]
