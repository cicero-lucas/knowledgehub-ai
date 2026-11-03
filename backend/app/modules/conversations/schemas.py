import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.modules.conversations.models import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    document_ids: List[uuid.UUID] = Field(
        default_factory=list,
        description="Documents to scope this conversation to. Empty = all user documents.",
    )


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime | None
    document_count: int = 0

    model_config = {"from_attributes": True}


class MessageSourceResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    page_number: int | None
    relevance_score: float | None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    sources: List[MessageSourceResponse] = []
    latency_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    document_ids: List[uuid.UUID] | None = Field(
        default=None,
        description="Override the conversation's document scope for this message.",
    )


class AskResponse(BaseModel):
    message: MessageResponse
    sources: List[MessageSourceResponse]
