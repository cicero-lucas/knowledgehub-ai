import uuid
from typing import List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.integrations.gemini.embeddings import embed_texts
from app.modules.rag.chunker import TextChunk
from app.modules.rag.models import DocumentChunk

logger = get_logger(__name__)


def embed_and_store_chunks(
    db: Session,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    chunks: List[TextChunk],
) -> List[DocumentChunk]:
    """
    Generate embeddings for all chunks and persist them to the database.

    Returns the list of persisted DocumentChunk ORM objects.
    """
    if not chunks:
        return []

    texts = [chunk.content for chunk in chunks]

    logger.info(
        "generating_embeddings",
        document_id=str(document_id),
        chunk_count=len(texts),
    )

    embeddings = embed_texts(texts)

    db_chunks: List[DocumentChunk] = []

    for chunk, embedding in zip(chunks, embeddings):
        db_chunk = DocumentChunk(
            document_id=document_id,
            user_id=user_id,
            content=chunk.content,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            embedding=embedding,
        )
        db.add(db_chunk)
        db_chunks.append(db_chunk)

    db.commit()

    logger.info(
        "embeddings_stored",
        document_id=str(document_id),
        stored_count=len(db_chunks),
    )
    return db_chunks
