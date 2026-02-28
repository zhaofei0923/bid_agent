"""PDF parser — extract text from PDF files using PyMuPDF."""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Threshold for detecting scanned/image PDFs (chars per page)
SCAN_THRESHOLD = 50


@dataclass
class ParsedPage:
    """Single page of extracted text."""

    page_number: int
    text: str
    is_scanned: bool = False


@dataclass
class ParsedDocument:
    """Full parsed document."""

    pages: list[ParsedPage]
    total_pages: int
    full_text: str
    metadata: dict
    has_scanned_pages: bool = False


def parse_pdf(file_path: str | Path) -> ParsedDocument:
    """Parse a PDF file and extract text from each page.

    Uses PyMuPDF (fitz) for text extraction. When a page has fewer than
    SCAN_THRESHOLD characters, it's flagged as a potential scan.

    Args:
        file_path: Path to the PDF file.

    Returns:
        ParsedDocument with page-level text and metadata.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed. Install with: pip install PyMuPDF")
        raise

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    doc = fitz.open(str(file_path))
    pages: list[ParsedPage] = []
    has_scanned = False

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        is_scanned = len(text.strip()) < SCAN_THRESHOLD

        if is_scanned:
            has_scanned = True
            logger.info(
                "Page %d appears scanned (%d chars), may need OCR",
                page_num + 1,
                len(text.strip()),
            )

        pages.append(
            ParsedPage(
                page_number=page_num + 1,
                text=text,
                is_scanned=is_scanned,
            )
        )

    full_text = "\n\n".join(p.text for p in pages)

    metadata = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "creator": doc.metadata.get("creator", ""),
        "page_count": doc.page_count,
    }
    doc.close()

    return ParsedDocument(
        pages=pages,
        total_pages=len(pages),
        full_text=full_text,
        metadata=metadata,
        has_scanned_pages=has_scanned,
    )


async def parse_pdf_async(file_path: str | Path) -> ParsedDocument:
    """Async wrapper around parse_pdf (runs in thread pool)."""
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, parse_pdf, file_path)
