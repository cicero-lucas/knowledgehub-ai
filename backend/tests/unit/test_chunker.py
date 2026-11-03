"""Unit tests for the RAG chunker."""

from app.modules.rag.chunker import TextChunk, chunk_pages
from app.modules.rag.extractor import PageContent


def _make_pages(texts: list[str]) -> list[PageContent]:
    return [PageContent(page_number=i + 1, text=t) for i, t in enumerate(texts)]


class TestChunker:
    def test_basic_chunking_produces_chunks(self):
        pages = _make_pages(["This is page one content. " * 50])
        chunks = chunk_pages(pages)
        assert len(chunks) > 0

    def test_chunk_preserves_page_number(self):
        pages = _make_pages(["Page one text. " * 100, "Page two text. " * 100])
        chunks = chunk_pages(pages)
        page_nums = {c.page_number for c in chunks}
        assert 1 in page_nums
        assert 2 in page_nums

    def test_chunk_indices_are_sequential(self):
        pages = _make_pages(["Content. " * 200])
        chunks = chunk_pages(pages)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_pages_returns_empty(self):
        chunks = chunk_pages([])
        assert chunks == []

    def test_whitespace_only_pages_skipped(self):
        pages = _make_pages(["   \n\t\n   "])
        chunks = chunk_pages(pages)
        assert chunks == []

    def test_short_fragment_skipped(self):
        # Fragments under 20 chars should be dropped
        pages = _make_pages(["Hi"])
        chunks = chunk_pages(pages)
        assert chunks == []

    def test_chunk_content_is_stripped(self):
        pages = _make_pages(["  Hello world content here.  " * 50])
        chunks = chunk_pages(pages)
        for chunk in chunks:
            assert chunk.content == chunk.content.strip()

    def test_chunk_type(self):
        pages = _make_pages(["Some content here. " * 60])
        chunks = chunk_pages(pages)
        for chunk in chunks:
            assert isinstance(chunk, TextChunk)
