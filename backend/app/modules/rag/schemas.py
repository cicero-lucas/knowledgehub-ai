import uuid

from pydantic import BaseModel


class ChunkSource(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    page_number: int | None
    relevance_score: float
