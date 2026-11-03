import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.documents.models import DocumentStatus


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    original_name: str
    file_size: int | None
    mime_type: str | None
    page_count: int | None
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: DocumentStatus
    error_message: str | None
    page_count: int | None

    model_config = {"from_attributes": True}
