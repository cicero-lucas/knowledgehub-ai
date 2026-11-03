import uuid
from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.documents.models import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        filename: str,
        original_name: str,
        file_path: str,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> Document:
        doc = Document(
            user_id=user_id,
            filename=filename,
            original_name=original_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def get_by_id_and_user(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document | None:
        return (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )

    def list_by_user(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> Tuple[List[Document], int]:
        query = self.db.query(Document).filter(Document.user_id == user_id)
        total = query.count()
        items = (
            query.order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total

    def update_status(
        self,
        document: Document,
        status: DocumentStatus,
        error_message: str | None = None,
        page_count: int | None = None,
    ) -> Document:
        document.status = status
        if error_message is not None:
            document.error_message = error_message
        if page_count is not None:
            document.page_count = page_count
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()

    def count_by_user(self, user_id: uuid.UUID) -> int:
        return (
            self.db.query(func.count(Document.id))
            .filter(Document.user_id == user_id)
            .scalar()
            or 0
        )

    def count_by_status(self, user_id: uuid.UUID) -> dict:
        rows = (
            self.db.query(Document.status, func.count(Document.id))
            .filter(Document.user_id == user_id)
            .group_by(Document.status)
            .all()
        )
        return {status.value: count for status, count in rows}
