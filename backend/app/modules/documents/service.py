import uuid

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.documents.models import Document, DocumentStatus
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.schemas import DocumentListResponse, DocumentResponse
from app.shared.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.shared.pagination import PaginatedResponse
from app.shared.storage import storage

logger = get_logger(__name__)

ALLOWED_MIME_TYPES = {"application/pdf"}


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DocumentRepository(db)

    def _validate_file(self, file: UploadFile) -> None:
        """Validate extension, MIME type, and size."""
        if not file.filename:
            raise ValidationError("Filename is required.")

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in settings.allowed_extensions_list:
            raise ValidationError(
                f"File type '.{ext}' is not allowed. Only PDF files are accepted."
            )

        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"MIME type '{file.content_type}' is not allowed."
            )

    async def upload(
        self,
        user_id: uuid.UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> Document:
        self._validate_file(file)

        content = await file.read()

        if len(content) > settings.max_upload_size_bytes:
            raise ValidationError(
                f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        filename = storage.generate_filename(file.filename)
        file_path = await storage.save(str(user_id), filename, content)

        doc = self.repo.create(
            user_id=user_id,
            filename=filename,
            original_name=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
        )

        # Kick off RAG pipeline asynchronously
        background_tasks.add_task(self._process_document, doc.id)

        logger.info(
            "document_uploaded",
            document_id=str(doc.id),
            user_id=str(user_id),
            filename=file.filename,
            size=len(content),
        )
        return doc

    def _process_document(self, document_id: uuid.UUID) -> None:
        """
        Background task: runs the full RAG ingestion pipeline.
        Imports are deferred to avoid circular dependencies.
        """
        from app.core.database import SessionLocal
        from app.modules.rag.pipeline import RAGPipeline

        with SessionLocal() as db:
            repo = DocumentRepository(db)
            doc = repo.get_by_id(document_id)
            if not doc:
                logger.error("document_not_found_for_processing", document_id=str(document_id))
                return

            repo.update_status(doc, DocumentStatus.PROCESSING)

            try:
                pipeline = RAGPipeline(db)
                pipeline.process(doc)
                logger.info("document_processed", document_id=str(document_id))
            except Exception as exc:
                logger.error(
                    "document_processing_failed",
                    document_id=str(document_id),
                    error=str(exc),
                )
                repo.update_status(
                    doc, DocumentStatus.FAILED, error_message=str(exc)
                )

    def get(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Document:
        doc = self.repo.get_by_id_and_user(document_id, user_id)
        if not doc:
            raise NotFoundError("Document", str(document_id))
        return doc

    def list(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[DocumentResponse]:
        offset = (page - 1) * page_size
        items, total = self.repo.list_by_user(user_id, offset=offset, limit=page_size)
        return PaginatedResponse.create(
            items=[DocumentResponse.model_validate(d) for d in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def delete(self, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        doc = self.get(document_id, user_id)
        file_path = doc.file_path
        self.repo.delete(doc)
        # Best-effort: remove file from storage
        import asyncio

        try:
            asyncio.get_event_loop().run_until_complete(storage.delete(file_path))
        except Exception:
            pass

    def reprocess(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        background_tasks: BackgroundTasks,
    ) -> Document:
        doc = self.get(document_id, user_id)

        if doc.status == DocumentStatus.PROCESSING:
            raise ValidationError("Document is already being processed.")

        # Reset existing chunks
        from app.modules.rag.models import DocumentChunk
        self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        self.db.commit()

        self.repo.update_status(doc, DocumentStatus.PENDING, error_message=None)
        background_tasks.add_task(self._process_document, document_id)
        self.db.refresh(doc)
        return doc
