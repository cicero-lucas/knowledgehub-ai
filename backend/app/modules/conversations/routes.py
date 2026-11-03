import uuid

from fastapi import APIRouter, Query, status

from app.core.database import DbSession
from app.modules.auth.dependencies import CurrentUser
from app.modules.conversations.schemas import (
    AskRequest,
    AskResponse,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
)
from app.modules.conversations.service import ConversationService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
)
def create_conversation(
    data: ConversationCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ConversationResponse:
    service = ConversationService(db)
    conv = service.create(current_user.id, data)
    r = ConversationResponse.model_validate(conv)
    r.document_count = len(conv.documents)
    return r


@router.get(
    "/",
    response_model=PaginatedResponse[ConversationResponse],
    summary="List conversations",
)
def list_conversations(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[ConversationResponse]:
    service = ConversationService(db)
    return service.list(current_user.id, page=page, page_size=page_size)


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation with messages",
)
def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ConversationDetailResponse:
    service = ConversationService(db)
    conv = service.get(conversation_id, current_user.id)
    messages = service.get_messages(conversation_id, current_user.id)
    result = ConversationDetailResponse.model_validate(conv)
    result.document_count = len(conv.documents)
    result.messages = messages
    return result


@router.post(
    "/{conversation_id}/messages",
    response_model=AskResponse,
    summary="Send a question and get a RAG-powered answer",
)
def ask(
    conversation_id: uuid.UUID,
    request: AskRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AskResponse:
    service = ConversationService(db)
    return service.ask(conversation_id, current_user.id, request)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="Get message history",
)
def get_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[MessageResponse]:
    service = ConversationService(db)
    return service.get_messages(conversation_id, current_user.id)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
)
def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = ConversationService(db)
    service.delete(conversation_id, current_user.id)
