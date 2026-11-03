import uuid
from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.conversations.models import (
    Conversation,
    Message,
    MessageRole,
    MessageSource,
)


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        title: str | None = None,
        documents: list | None = None,
    ) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        if documents:
            conv.documents = documents
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        return self.db.get(Conversation, conversation_id)

    def get_by_id_and_user(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation | None:
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .first()
        )

    def list_by_user(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> Tuple[List[Conversation], int]:
        query = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        )
        total = query.count()
        items = (
            query.order_by(Conversation.updated_at.desc().nullslast(),
                           Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total

    def delete(self, conversation: Conversation) -> None:
        self.db.delete(conversation)
        self.db.commit()

    def count_by_user(self, user_id: uuid.UUID) -> int:
        return (
            self.db.query(func.count(Conversation.id))
            .filter(Conversation.user_id == user_id)
            .scalar()
            or 0
        )

    def update_title(self, conversation: Conversation, title: str) -> Conversation:
        conversation.title = title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation


class MessageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user_message(
        self, conversation_id: uuid.UUID, content: str
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def create_assistant_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        latency_ms: int | None = None,
        sources_data: list | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            latency_ms=latency_ms,
        )
        self.db.add(msg)
        self.db.flush()  # Get the message ID before adding sources

        if sources_data:
            for source in sources_data:
                ms = MessageSource(
                    message_id=msg.id,
                    chunk_id=source.get("chunk_id"),
                    document_id=source["document_id"],
                    document_name=source["document_name"],
                    page_number=source.get("page_number"),
                    relevance_score=source.get("relevance_score"),
                )
                self.db.add(ms)

        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, conversation_id: uuid.UUID) -> List[Message]:
        return (
            self.db.query(Message)
            .options(joinedload(Message.sources))
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )

    def count_by_user(self, user_id: uuid.UUID) -> int:
        """Count total messages sent by user (user role only)."""
        return (
            self.db.query(func.count(Message.id))
            .join(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Message.role == MessageRole.USER,
            )
            .scalar()
            or 0
        )
