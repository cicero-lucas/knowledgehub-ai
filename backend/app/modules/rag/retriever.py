import uuid
from dataclasses import dataclass
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.gemini.embeddings import embed_query
from app.modules.rag.models import DocumentChunk
from app.modules.documents.models import Document

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    page_number: int | None
    content: str
    relevance_score: float


def retrieve_relevant_chunks(
    db: Session,
    question: str,
    user_id: uuid.UUID,
    document_ids: List[uuid.UUID] | None = None,
    top_k: int | None = None,
    similarity_threshold: float | None = None,
) -> List[RetrievedChunk]:
    """
    Semantic search: find the most relevant chunks for a question.

    Args:
        db: Database session.
        question: Natural language query.
        user_id: Restricts search to chunks owned by this user.
        document_ids: Optional whitelist of specific documents to search.
        top_k: Number of results to return (defaults to settings.RAG_TOP_K).
        similarity_threshold: Minimum cosine similarity (0-1).

    Returns:
        List of RetrievedChunk sorted by relevance (most relevant first).
    """
    k = top_k or settings.RAG_TOP_K
    threshold = similarity_threshold or settings.RAG_SIMILARITY_THRESHOLD

    # Embed the query
    query_embedding = embed_query(question)
    embedding_str = f"[{','.join(str(v) for v in query_embedding)}]"

    # Build filter conditions
    conditions = ["dc.user_id = :user_id"]
    params: dict = {"user_id": str(user_id), "top_k": k, "threshold": threshold}

    if document_ids:
        # Convert UUIDs to strings for parameterized query
        doc_id_strings = [str(did) for did in document_ids]
        conditions.append("dc.document_id = ANY(:document_ids)")
        params["document_ids"] = doc_id_strings

    where_clause = " AND ".join(conditions)

    # pgvector cosine distance: lower = more similar; similarity = 1 - distance
    sql = text(f"""
        SELECT
            dc.id            AS chunk_id,
            dc.document_id,
            d.original_name  AS document_name,
            dc.page_number,
            dc.content,
            1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE {where_clause}
          AND (1 - (dc.embedding <=> CAST(:embedding AS vector))) >= :threshold
        ORDER BY dc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    params["embedding"] = embedding_str

    rows = db.execute(sql, params).fetchall()

    results = [
        RetrievedChunk(
            chunk_id=uuid.UUID(str(row.chunk_id)),
            document_id=uuid.UUID(str(row.document_id)),
            document_name=row.document_name,
            page_number=row.page_number,
            content=row.content,
            relevance_score=float(row.similarity),
        )
        for row in rows
    ]

    logger.info(
        "retrieval_complete",
        question_length=len(question),
        user_id=str(user_id),
        results_count=len(results),
        top_k=k,
        threshold=threshold,
    )
    return results
