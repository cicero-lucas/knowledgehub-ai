from fastapi import APIRouter

from app.core.database import DbSession
from app.modules.auth.dependencies import CurrentUser
from app.modules.conversations.repository import ConversationRepository, MessageRepository
from app.modules.documents.repository import DocumentRepository
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_documents: int
    total_conversations: int
    total_queries: int
    documents_by_status: dict[str, int]


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats, summary="Get user dashboard statistics")
def get_stats(current_user: CurrentUser, db: DbSession) -> DashboardStats:
    doc_repo = DocumentRepository(db)
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    return DashboardStats(
        total_documents=doc_repo.count_by_user(current_user.id),
        total_conversations=conv_repo.count_by_user(current_user.id),
        total_queries=msg_repo.count_by_user(current_user.id),
        documents_by_status=doc_repo.count_by_status(current_user.id),
    )
