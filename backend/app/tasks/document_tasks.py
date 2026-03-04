"""Document processing tasks — PDF parsing, chunking, vectorization."""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.agents.embedding_client import get_embedding_client
from app.database import async_session
from app.models.bid_document import BidDocument, BidDocumentChunk, BidDocumentSection
from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ── Chunking Strategy ──────────────────────────────────


class DocumentChunker:
    """RecursiveCharacterTextSplitter-style document chunker."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def chunk_text(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> list[dict]:
        """Split text into overlapping chunks.

        Args:
            text: Full document text.
            metadata: Dict merged into each chunk (e.g. section_id, page_number).

        Returns:
            List of dicts: {content, chunk_index, char_start, char_end, **metadata}
        """
        if not text:
            return []

        meta = metadata or {}
        chunks: list[dict] = []
        splits = self._recursive_split(text, self.separators)

        # Merge small splits into overlapping chunks
        current_chunk = ""
        current_start = 0
        char_pos = 0

        for split in splits:
            if len(current_chunk) + len(split) > self.chunk_size and current_chunk:
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "chunk_index": len(chunks),
                        "char_start": current_start,
                        "char_end": char_pos,
                        **meta,
                    }
                )
                # Overlap: keep the last `chunk_overlap` characters
                overlap = current_chunk[-self.chunk_overlap :] if self.chunk_overlap else ""
                current_chunk = overlap + split
                current_start = char_pos - len(overlap)
            else:
                current_chunk += split
            char_pos += len(split)

        # Last chunk
        if current_chunk.strip():
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "chunk_index": len(chunks),
                    "char_start": current_start,
                    "char_end": char_pos,
                    **meta,
                }
            )

        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Split text recursively using the separator hierarchy."""
        if not separators:
            return [text]

        sep = separators[0]
        parts = text.split(sep)

        result: list[str] = []
        for i, part in enumerate(parts):
            if len(part) > self.chunk_size and len(separators) > 1:
                result.extend(self._recursive_split(part, separators[1:]))
            else:
                result.append(part + (sep if i < len(parts) - 1 else ""))

        return result


# ── Async Processing ───────────────────────────────────


async def _parse_pdf(file_path: str) -> list[dict]:
    """Parse PDF using pdfplumber, returning pages with text.

    Returns:
        List of {page_number, text} dicts.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber not installed — run: pip install pdfplumber")
        return []

    pages = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append({"page_number": i + 1, "text": text})
    except Exception:
        logger.exception("Failed to parse PDF: %s", file_path)

    return pages


async def _process_document(document_id: str) -> dict:
    """Parse, chunk, and vectorize a bid document."""
    embedding_client = get_embedding_client()
    chunker = DocumentChunker()

    async with async_session() as db:
        # 1. Load the document
        result = await db.execute(
            select(BidDocument).where(BidDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        # Update status to processing
        doc.status = "processing"
        doc.processing_progress = 5
        await db.commit()

        pages: list[dict] = []
        section_tuples: list[tuple] = []
        all_chunk_records: list[dict] = []
        total_vectorized = 0

        try:
            # 2. Parse PDF → pages
            pages = await _parse_pdf(doc.file_path)
            if not pages:
                logger.warning("Document %s has no parseable content", document_id)
                doc.status = "error"
                doc.error_message = "PDF parsing failed or no text content found"
                await db.commit()
                return {"status": "error", "reason": "no_content"}

            doc.page_count = len(pages)
            doc.processing_progress = 20
            await db.commit()

            # 3. Delete old sections/chunks (in case of re-processing)
            old_sections = await db.execute(
                select(BidDocumentSection).where(
                    BidDocumentSection.bid_document_id == document_id
                )
            )
            for section in old_sections.scalars().all():
                await db.delete(section)
            await db.commit()

            # 4. Create sections — one per page group or logical section
            # Simple strategy: group pages into 5-page sections
            group_size = 5
            for start_idx in range(0, len(pages), group_size):
                page_group = pages[start_idx : start_idx + group_size]
                content = "\n\n".join(
                    f"=== 第{p['page_number']}页 ===\n{p['text']}"
                    for p in page_group
                    if p["text"].strip()
                )
                if not content.strip():
                    continue

                section = BidDocumentSection(
                    bid_document_id=doc.id,
                    section_type="full_document",
                    section_title=f"第{page_group[0]['page_number']}-{page_group[-1]['page_number']}页",
                    start_page=page_group[0]["page_number"],
                    end_page=page_group[-1]["page_number"],
                    content_preview=content[:500],
                )
                db.add(section)
                section_tuples.append((section, content))

            await db.flush()  # Assign IDs to sections

            doc.processing_progress = 40
            await db.commit()

            # 5. Chunk each section
            for section, content in section_tuples:
                section_chunks = chunker.chunk_text(
                    content,
                    metadata={
                        "section_id": str(section.id),
                        "section_type": section.section_type,
                        "page_number": section.start_page,
                    },
                )
                all_chunk_records.extend(section_chunks)

            doc.chunk_count = len(all_chunk_records)
            doc.processing_progress = 60
            await db.commit()

            # 6. Vectorize chunks in batches
            total_vectorized = 0
            batch_size = 16
            for i in range(0, len(all_chunk_records), batch_size):
                batch = all_chunk_records[i : i + batch_size]
                texts = [c["content"] for c in batch]

                try:
                    embeddings = await embedding_client.embed_texts(texts)

                    for chunk_data, emb_result in zip(batch, embeddings):
                        db_chunk = BidDocumentChunk(
                            bid_document_id=doc.id,
                            project_id=doc.project_id,
                            section_id=chunk_data.get("section_id"),
                            content=chunk_data["content"],
                            chunk_index=chunk_data["chunk_index"],
                            page_number=chunk_data.get("page_number", 1),
                            start_char=chunk_data.get("char_start"),
                            end_char=chunk_data.get("char_end"),
                            section_type=chunk_data.get("section_type"),
                            embedding=emb_result.embedding,
                        )
                        db.add(db_chunk)
                        total_vectorized += 1

                    await db.flush()

                except Exception:
                    logger.warning(
                        "Vectorization failed for batch %d-%d", i, i + batch_size,
                        exc_info=True,
                    )

            doc.vectorized_chunk_count = total_vectorized
            doc.processing_progress = 90
            await db.commit()

        except Exception:
            logger.exception("Processing failed for document %s", document_id)
            doc.status = "error"
            doc.error_message = "Internal processing error"
            await db.commit()
            return {"status": "error", "reason": "internal_error"}

        # 7. Update document to processed
        doc.status = "processed"
        doc.processing_progress = 100
        doc.processed_at = datetime.now(UTC)
        await db.commit()

    return {
        "document_id": document_id,
        "pages": len(pages) if pages else 0,
        "sections": len(section_tuples) if "section_tuples" in dir() else 0,
        "chunks": len(all_chunk_records) if "all_chunk_records" in dir() else 0,
        "vectorized": total_vectorized if "total_vectorized" in dir() else 0,
        "status": "processed",
    }


# ── Celery Tasks ───────────────────────────────────────


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_document(self, document_id: str) -> dict:
    """Process a bid document: parse → chunk → vectorize.

    Called after file upload completes.
    """
    logger.info("Processing document %s", document_id)
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _process_document(document_id)
        )
        logger.info("Document %s processed: %s", document_id, result)
        return result
    except Exception as exc:
        logger.exception("Failed to process document %s", document_id)
        raise self.retry(exc=exc) from exc


@celery_app.task
def process_all_pending() -> list[str]:
    """Find and process all pending documents."""

    async def _find_pending() -> list[str]:
        async with async_session() as db:
            result = await db.execute(
                select(BidDocument.id).where(BidDocument.status == "pending")
            )
            return [str(row[0]) for row in result.all()]

    pending_ids = asyncio.get_event_loop().run_until_complete(_find_pending())
    for doc_id in pending_ids:
        process_document.delay(doc_id)

    logger.info("Queued %d pending documents for processing", len(pending_ids))
    return pending_ids
