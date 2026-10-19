import asyncio

class DocumentIndex:
    def __init__(self, entries: dict[tuple[str, str], tuple[str, ...]]):
        self.entries = entries

    async def search(self, tenant_id: str, normalized_question: str):
        await asyncio.sleep(0)
        return self.entries.get((tenant_id, normalized_question), ())
