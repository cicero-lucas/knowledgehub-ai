import uuid

from fastapi import APIRouter, BackgroundTasks, File, Query, UploadFile, status

from app.core.database import DbSession
from app.modules.auth.dependencies import CurrentUser
from app.modules.documents.schemas import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from app.modules.documents.service import DocumentService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: CurrentUser = None,
    db: DbSession = None,
) -> DocumentResponse:
    service = DocumentService(db)
    doc = await service.upload(current_user.id, file, background_tasks)
    return DocumentResponse.model_validate(doc)


@router.get(
    "/",
    response_model=PaginatedResponse[DocumentResponse],
    summary="List user documents",
)
def list_documents(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[DocumentResponse]:
    service = DocumentService(db)
    return service.list(current_user.id, page=page, page_size=page_size)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
)
def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentResponse:
    service = DocumentService(db)
    doc = service.get(document_id, current_user.id)
    return DocumentResponse.model_validate(doc)


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Get document processing status",
)
def get_document_status(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentStatusResponse:
    service = DocumentService(db)
    doc = service.get(document_id, current_user.id)
    return DocumentStatusResponse.model_validate(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
def delete_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = DocumentService(db)
    service.delete(document_id, current_user.id)


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentResponse,
    summary="Reprocess a document through the RAG pipeline",
)
def reprocess_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentResponse:
    service = DocumentService(db)
    doc = service.reprocess(document_id, current_user.id, background_tasks)
    return DocumentResponse.model_validate(doc)
