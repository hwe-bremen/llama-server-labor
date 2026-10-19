from .index import DocumentIndex

class Retriever:
    def __init__(self, index: DocumentIndex):
        self.index = index
        self._cache: dict[str, tuple[str, ...]] = {}

    async def retrieve(self, tenant_id: str, question: str) -> tuple[str, ...]:
        key = question.strip().casefold()
        if key not in self._cache:
            self._cache[key] = await self.index.search(tenant_id, key)
        return self._cache[key]
