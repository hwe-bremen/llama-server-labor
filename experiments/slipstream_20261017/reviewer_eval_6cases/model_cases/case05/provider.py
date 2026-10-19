import asyncio
from typing import Protocol

class Client(Protocol):
    async def generate(self, prompt: str) -> str: ...

class LimitedProvider:
    def __init__(self, client: Client, parallel: int = 1):
        if parallel < 1:
            raise ValueError("parallel must be positive")
        self.client = client
        self._slots = asyncio.Semaphore(parallel)

    async def complete(self, prompt: str) -> str:
        async with self._slots:
            return await self.client.generate(prompt)
