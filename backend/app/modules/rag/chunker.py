from dataclasses import dataclass
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.rag.extractor import PageContent

logger = get_logger(__name__)


@dataclass
class TextChunk:
    content: str
    page_number: int
    chunk_index: int   # Global index within the document


def chunk_pages(pages: List[PageContent]) -> List[TextChunk]:
    """
    Split page-level text into overlapping chunks suitable for embedding.

    Strategy:
    - Use RecursiveCharacterTextSplitter to respect natural text boundaries.
    - Each chunk preserves the page_number it originated from.
    - chunk_index is a global sequential counter across the whole document.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks: List[TextChunk] = []
    global_index = 0

    for page in pages:
        if not page.text.strip():
            continue

        raw_chunks = splitter.split_text(page.text)

        for raw in raw_chunks:
            cleaned = raw.strip()
            if len(cleaned) < 20:  # Skip near-empty fragments
                continue
            all_chunks.append(
                TextChunk(
                    content=cleaned,
                    page_number=page.page_number,
                    chunk_index=global_index,
                )
            )
            global_index += 1

    logger.info(
        "chunking_complete",
        input_pages=len(pages),
        output_chunks=len(all_chunks),
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    return all_chunks
