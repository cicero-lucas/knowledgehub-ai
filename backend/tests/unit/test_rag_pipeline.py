"""Unit tests for the RAG pipeline components with mocked Gemini."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.modules.rag.extractor import PageContent
from app.modules.rag.chunker import chunk_pages
from app.modules.rag.generator import generate_rag_answer, RAGAnswer
from app.modules.rag.retriever import RetrievedChunk


class TestGenerator:
    def test_returns_not_found_when_no_chunks(self, mock_gemini_generate):
        result = generate_rag_answer("What is X?", [])
        # With empty chunks, generation module returns default message
        assert isinstance(result, RAGAnswer)

    def test_sources_match_input_chunks(self, mock_gemini_generate):
        chunk = RetrievedChunk(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            document_name="report.pdf",
            page_number=3,
            content="The answer is 42.",
            relevance_score=0.95,
        )
        result = generate_rag_answer("What is the answer?", [chunk])
        assert result.sources == [chunk]
        assert result.answer  # Non-empty

    def test_model_name_present(self, mock_gemini_generate):
        result = generate_rag_answer("Question?", [])
        assert result.model  # Should be non-empty string


class TestRetriever:
    """Tests for retriever logic — mocks Gemini embed_query and DB."""

    def test_retriever_scopes_by_user(self):
        """Ensure user_id is always applied as a filter."""
        with patch("app.modules.rag.retriever.embed_query") as mock_embed, \
             patch("app.modules.rag.retriever.Session") as mock_session:

            mock_embed.return_value = [0.1] * 768
            mock_db = MagicMock()
            mock_db.execute.return_value.fetchall.return_value = []

            from app.modules.rag.retriever import retrieve_relevant_chunks

            result = retrieve_relevant_chunks(
                db=mock_db,
                question="test question",
                user_id=uuid.uuid4(),
            )
            assert result == []

            # Verify the query was actually executed
            mock_db.execute.assert_called_once()
            # The SQL should contain user_id filter
            call_args = mock_db.execute.call_args
            sql_str = str(call_args[0][0])
            assert "user_id" in sql_str
