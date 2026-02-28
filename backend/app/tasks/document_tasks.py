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

        # 2. Parse PDF → text (placeholder: assume parsed_content exists)
        parsed_text = doc.parsed_content or ""
        if not parsed_text:
            logger.warning("Document %s has no parsed content", document_id)
            doc.status = "error"
            await db.commit()
            return {"status": "error", "reason": "no_content"}

        # 3. Create sections (if not already parsed into sections)
        result = await db.execute(
            select(BidDocumentSection).where(
                BidDocumentSection.document_id == document_id
            )
        )
        sections = result.scalars().all()

        if not sections:
            # Create a single section for the whole document
            section = BidDocumentSection(
                document_id=document_id,
                section_type="full_document",
                title=doc.original_filename or "Full Document",
                content=parsed_text,
                page_start=1,
                page_end=1,
                order_index=0,
            )
            db.add(section)
            await db.flush()
            sections = [section]

        # 4. Chunk each section
        all_chunks: list[dict] = []
        for section in sections:
            section_text = section.content or ""
            section_chunks = chunker.chunk_text(
                section_text,
                metadata={
                    "section_id": str(section.id),
                    "section_type": section.section_type,
                    "page_number": section.page_start or 1,
                },
            )
            all_chunks.extend(section_chunks)

        # 5. Vectorize chunks
        texts = [c["content"] for c in all_chunks]
        if texts:
            embeddings = await embedding_client.embed_texts(texts)

            for chunk, emb_result in zip(all_chunks, embeddings):
                db_chunk = BidDocumentChunk(
                    section_id=chunk["section_id"],
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    page_number=chunk.get("page_number", 1),
                    embedding=emb_result.embedding,
                )
                db.add(db_chunk)

        # 6. Update document status
        doc.status = "processed"
        doc.vectorized_chunk_count = len(all_chunks)
        doc.updated_at = datetime.now(UTC)

        await db.commit()

    return {
        "document_id": document_id,
        "sections": len(sections),
        "chunks": len(all_chunks),
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
        raise self.retry(exc=exc)


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
