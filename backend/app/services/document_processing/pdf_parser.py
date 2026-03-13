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


async def enhance_scanned_pages(
    parsed_doc: ParsedDocument,
    file_path: str | Path,
) -> ParsedDocument:
    """Use Tencent Cloud OCR to fill in text for scanned pages.

    Only activates when:
    1. TENCENT_OCR_ENABLED is True in settings
    2. The document has scanned pages (is_scanned=True)

    Non-scanned pages are left untouched.
    Returns a new ParsedDocument with OCR text merged in.
    """
    from app.services.document_processing.tencent_doc_parser import (
        get_tencent_doc_parser,
    )

    if not parsed_doc.has_scanned_pages:
        return parsed_doc

    parser = get_tencent_doc_parser()
    if parser is None:
        logger.info("Tencent OCR not available — %d scanned pages skipped",
                    sum(1 for p in parsed_doc.pages if p.is_scanned))
        return parsed_doc

    scanned_page_nums = [p.page_number for p in parsed_doc.pages if p.is_scanned]
    logger.info(
        "Sending %d scanned pages to Tencent OCR: %s",
        len(scanned_page_nums), scanned_page_nums,
    )

    ocr_results = await parser.ocr_pdf_pages(
        file_path, scanned_page_nums, concurrency=3
    )

    # Merge OCR text back into pages
    enhanced_pages: list[ParsedPage] = []
    ocr_recovered = 0
    for page in parsed_doc.pages:
        if page.is_scanned and page.page_number in ocr_results:
            ocr_text = ocr_results[page.page_number]
            if ocr_text.strip():
                enhanced_pages.append(ParsedPage(
                    page_number=page.page_number,
                    text=ocr_text,
                    is_scanned=False,  # Successfully OCR'd
                ))
                ocr_recovered += 1
                continue
        enhanced_pages.append(page)

    logger.info(
        "Tencent OCR recovered %d/%d scanned pages",
        ocr_recovered, len(scanned_page_nums),
    )

    full_text = "\n\n".join(p.text for p in enhanced_pages)
    has_remaining_scanned = any(p.is_scanned for p in enhanced_pages)

    return ParsedDocument(
        pages=enhanced_pages,
        total_pages=parsed_doc.total_pages,
        full_text=full_text,
        metadata=parsed_doc.metadata,
        has_scanned_pages=has_remaining_scanned,
    )
