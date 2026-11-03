"""
RAG Ingestion Pipeline
Orchestrates: Extract → Chunk → Embed → Store
Called as a background task after document upload.
"""

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.modules.documents.models import Document, DocumentStatus
from app.modules.documents.repository import DocumentRepository
from app.modules.rag.chunker import chunk_pages
from app.modules.rag.embedder import embed_and_store_chunks
from app.modules.rag.extractor import extract_text_from_pdf, get_page_count
from app.shared.exceptions import DocumentProcessingError
from app.shared.storage import storage

logger = get_logger(__name__)


class RAGPipeline:
    """Orchestrates the document ingestion pipeline."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)

    def process(self, document: Document) -> None:
        """
        Full pipeline:
        1. Extract text from PDF (page by page)
        2. Chunk text with metadata
        3. Embed chunks via Gemini
        4. Store vectors in PostgreSQL (pgvector)
        5. Update document status
        """
        logger.info(
            "pipeline_start",
            document_id=str(document.id),
            file=document.original_name,
        )

        # ── Step 1: Extract ────────────────────────────────────────────────────
        file_path = document.file_path
        if not storage.exists(file_path):
            raise DocumentProcessingError(f"File not found in storage: {file_path}")

        pages = extract_text_from_pdf(file_path)
        page_count = get_page_count(file_path)

        # Update page count immediately
        self.doc_repo.update_status(
            document,
            DocumentStatus.PROCESSING,
            page_count=page_count,
        )

        # ── Step 2: Chunk ──────────────────────────────────────────────────────
        chunks = chunk_pages(pages)

        if not chunks:
            raise DocumentProcessingError(
                "No text chunks could be generated from the document."
            )

        # ── Step 3 & 4: Embed + Store ──────────────────────────────────────────
        embed_and_store_chunks(
            db=self.db,
            document_id=document.id,
            user_id=document.user_id,
            chunks=chunks,
        )

        # ── Step 5: Mark as completed ──────────────────────────────────────────
        self.doc_repo.update_status(
            document,
            DocumentStatus.COMPLETED,
            page_count=page_count,
        )

        logger.info(
            "pipeline_complete",
            document_id=str(document.id),
            pages=page_count,
            chunks=len(chunks),
        )
