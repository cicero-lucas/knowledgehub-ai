import time
import uuid
from typing import List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.modules.conversations.models import Conversation, Message
from app.modules.conversations.repository import ConversationRepository, MessageRepository
from app.modules.conversations.schemas import (
    AskRequest,
    AskResponse,
    ConversationCreate,
    MessageResponse,
    MessageSourceResponse,
)
from app.modules.documents.repository import DocumentRepository
from app.modules.rag.generator import generate_rag_answer
from app.modules.rag.retriever import retrieve_relevant_chunks
from app.shared.exceptions import ForbiddenError, NotFoundError, ValidationError

logger = get_logger(__name__)


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)
        self.doc_repo = DocumentRepository(db)

    def create(self, user_id: uuid.UUID, data: ConversationCreate) -> Conversation:
        documents = []
        if data.document_ids:
            for doc_id in data.document_ids:
                doc = self.doc_repo.get_by_id_and_user(doc_id, user_id)
                if not doc:
                    raise NotFoundError("Document", str(doc_id))
                documents.append(doc)

        title = data.title or "New conversation"
        return self.conv_repo.create(
            user_id=user_id, title=title, documents=documents
        )

    def get(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation:
        conv = self.conv_repo.get_by_id_and_user(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Conversation", str(conversation_id))
        return conv

    def list(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ):
        from app.shared.pagination import PaginatedResponse
        from app.modules.conversations.schemas import ConversationResponse

        offset = (page - 1) * page_size
        items, total = self.conv_repo.list_by_user(user_id, offset=offset, limit=page_size)

        response_items = []
        for conv in items:
            r = ConversationResponse.model_validate(conv)
            r.document_count = len(conv.documents)
            response_items.append(r)

        return PaginatedResponse.create(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def delete(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        conv = self.get(conversation_id, user_id)
        self.conv_repo.delete(conv)

    def get_messages(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[MessageResponse]:
        self.get(conversation_id, user_id)  # Ensure ownership
        messages = self.msg_repo.get_messages(conversation_id)
        return [MessageResponse.model_validate(m) for m in messages]

    def ask(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        request: AskRequest,
    ) -> AskResponse:
        """
        Full RAG query cycle:
        1. Save user message
        2. Retrieve relevant chunks (scoped to user + conversation docs)
        3. Generate grounded answer via Gemini
        4. Save assistant message with source attribution
        5. Return response
        """
        conv = self.get(conversation_id, user_id)

        # Determine which documents to search
        scope_doc_ids: List[uuid.UUID] | None = None
        if request.document_ids:
            # Per-message override — validate ownership
            scope_doc_ids = []
            for doc_id in request.document_ids:
                doc = self.doc_repo.get_by_id_and_user(doc_id, user_id)
                if not doc:
                    raise NotFoundError("Document", str(doc_id))
                scope_doc_ids.append(doc_id)
        elif conv.documents:
            scope_doc_ids = [d.id for d in conv.documents]
        # If neither: search across ALL user documents

        # Auto-generate title from first question
        if not conv.title or conv.title == "New conversation":
            short_title = request.question[:80]
            self.conv_repo.update_title(conv, short_title)

        # Save user message
        self.msg_repo.create_user_message(conversation_id, request.question)

        # Retrieve
        start_ts = time.monotonic()
        retrieved = retrieve_relevant_chunks(
            db=self.db,
            question=request.question,
            user_id=user_id,
            document_ids=scope_doc_ids,
        )

        # Generate
        rag_answer = generate_rag_answer(
            question=request.question,
            retrieved_chunks=retrieved,
        )

        latency_ms = int((time.monotonic() - start_ts) * 1000)

        # Build sources payload for persistence
        sources_data = [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "relevance_score": chunk.relevance_score,
            }
            for chunk in retrieved
        ]

        # Deduplicate sources by (document_id, page_number)
        seen = set()
        unique_sources_data = []
        for s in sources_data:
            key = (s["document_id"], s["page_number"])
            if key not in seen:
                seen.add(key)
                unique_sources_data.append(s)

        assistant_msg = self.msg_repo.create_assistant_message(
            conversation_id=conversation_id,
            content=rag_answer.answer,
            latency_ms=latency_ms,
            sources_data=unique_sources_data,
        )

        logger.info(
            "rag_answer_generated",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            chunks_retrieved=len(retrieved),
            latency_ms=latency_ms,
        )

        return AskResponse(
            message=MessageResponse.model_validate(assistant_msg),
            sources=[MessageSourceResponse.model_validate(s) for s in assistant_msg.sources],
        )
