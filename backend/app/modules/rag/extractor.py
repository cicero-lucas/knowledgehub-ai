from dataclasses import dataclass
from pathlib import Path
from typing import List

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.logging import get_logger
from app.shared.exceptions import DocumentProcessingError

logger = get_logger(__name__)


@dataclass
class PageContent:
    page_number: int   # 1-indexed
    text: str


def extract_text_from_pdf(file_path: str) -> List[PageContent]:
    """
    Extract text content from a PDF, page by page.

    Returns a list of PageContent objects preserving page numbers.
    Raises DocumentProcessingError for encrypted/unreadable PDFs.
    """
    path = Path(file_path)
    if not path.exists():
        raise DocumentProcessingError(f"File not found: {file_path}")

    try:
        reader = PdfReader(str(path))
    except PdfReadError as exc:
        raise DocumentProcessingError(f"Could not read PDF: {exc}") from exc

    if reader.is_encrypted:
        raise DocumentProcessingError(
            "PDF is encrypted/password-protected and cannot be processed."
        )

    pages: List[PageContent] = []
    total_pages = len(reader.pages)

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append(PageContent(page_number=page_num, text=text))
        except Exception as exc:
            logger.warning(
                "page_extraction_failed",
                page=page_num,
                total=total_pages,
                error=str(exc),
            )
            continue

    if not pages:
        raise DocumentProcessingError(
            "No extractable text found in the PDF. "
            "The document may be a scanned image or contain only non-text elements."
        )

    logger.info(
        "pdf_extracted",
        file=file_path,
        total_pages=total_pages,
        pages_with_text=len(pages),
    )
    return pages


def get_page_count(file_path: str) -> int:
    """Return the total number of pages in a PDF."""
    try:
        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception:
        return 0
