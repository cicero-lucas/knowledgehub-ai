from dataclasses import dataclass
from typing import List

from app.integrations.gemini.generation import GenerationResult, generate_answer
from app.modules.rag.retriever import RetrievedChunk


@dataclass
class RAGAnswer:
    answer: str
    sources: List[RetrievedChunk]
    model: str


def generate_rag_answer(
    question: str,
    retrieved_chunks: List[RetrievedChunk],
) -> RAGAnswer:
    """
    Generate a grounded answer from retrieved document chunks.

    Args:
        question: The user's question.
        retrieved_chunks: Relevant chunks from the retriever.

    Returns:
        RAGAnswer with the generated text and source attribution.
    """
    context_dicts = [
        {
            "content": chunk.content,
            "document_name": chunk.document_name,
            "page_number": chunk.page_number or "N/A",
        }
        for chunk in retrieved_chunks
    ]

    result: GenerationResult = generate_answer(question, context_dicts)

    return RAGAnswer(
        answer=result.answer,
        sources=retrieved_chunks,
        model=result.model,
    )
