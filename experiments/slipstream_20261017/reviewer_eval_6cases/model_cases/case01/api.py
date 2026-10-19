from dataclasses import dataclass
from .retrieval import Retriever

@dataclass(frozen=True)
class Identity:
    tenant_id: str

async def context_for(identity: Identity, question: str, retriever: Retriever):
    return await retriever.retrieve(identity.tenant_id, question)
