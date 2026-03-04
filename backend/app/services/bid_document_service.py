"""Bid document service — upload, parse, search, manage bid documents."""

import hashlib
import logging
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.bid_document import BidDocument, BidDocumentChunk, BidDocumentSection

logger = logging.getLogger(__name__)
settings = get_settings()


class BidDocumentService:
    """Service for bid document lifecycle: upload → parse → search."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload(
        self,
        project_id: UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> BidDocument:
        """Upload and register a bid document.

        File is saved to disk and a DB record created with status='pending'.
        The actual parsing + vectorization is handled by Celery tasks.
        """
        # Validate file type
        allowed_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if content_type not in allowed_types:
            raise ValidationError(f"Unsupported file type: {content_type}")

        # Validate file size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(
                f"File too large: {len(content)} bytes (max {max_bytes})"
            )

        # Compute SHA256 hash
        file_hash = hashlib.sha256(content).hexdigest()

        # Check for duplicates
        result = await self.db.execute(
            select(BidDocument).where(
                BidDocument.project_id == project_id,
                BidDocument.file_hash == file_hash,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValidationError("Duplicate file: document already uploaded")

        # Save to disk
        upload_dir = Path(settings.UPLOAD_DIR) / str(project_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename

        with open(file_path, "wb") as f:
            f.write(content)

        # Create DB record
        doc = BidDocument(
            project_id=project_id,
            filename=filename,
            original_filename=filename,
            file_path=str(file_path),
            file_size=len(content),
            file_hash=file_hash,
            status="pending",
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        logger.info(
            "Uploaded document %s for project %s (%d bytes)",
            doc.id, project_id, len(content),
        )
        return doc

    async def get_by_id(self, document_id: UUID) -> BidDocument:
        """Get a document by ID."""
        result = await self.db.execute(
            select(BidDocument).where(BidDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError("BidDocument", str(document_id))
        return doc

    async def list_by_project(self, project_id: UUID) -> list[BidDocument]:
        """List all documents for a project."""
        result = await self.db.execute(
            select(BidDocument)
            .where(BidDocument.project_id == project_id)
            .order_by(BidDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_sections(self, document_id: UUID) -> list[BidDocumentSection]:
        """Get all sections for a document."""
        result = await self.db.execute(
            select(BidDocumentSection)
            .where(BidDocumentSection.bid_document_id == document_id)
            .order_by(BidDocumentSection.start_page)
        )
        return list(result.scalars().all())

    async def delete(self, document_id: UUID) -> None:
        """Delete a document and remove its file from disk.

        Uses raw SQL DELETE to avoid ORM session conflicts caused by
        lazy="selectin" pre-loading child objects into the session.
        DB ON DELETE CASCADE handles sections/chunks automatically.
        """
        # Fetch file_path only — noload prevents selectin from loading sections
        result = await self.db.execute(
            select(BidDocument)
            .where(BidDocument.id == document_id)
            .options(noload(BidDocument.sections), noload(BidDocument.chunks))
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError("BidDocument", str(document_id))

        file_path = doc.file_path

        # Expunge from session before raw SQL to avoid stale-state conflicts
        self.db.expunge(doc)

        # Raw SQL DELETE — DB CASCADE removes sections and chunks
        await self.db.execute(
            sql_delete(BidDocumentChunk).where(
                BidDocumentChunk.bid_document_id == document_id
            )
        )
        await self.db.execute(
            sql_delete(BidDocumentSection).where(
                BidDocumentSection.bid_document_id == document_id
            )
        )
        await self.db.execute(
            sql_delete(BidDocument).where(BidDocument.id == document_id)
        )
        await self.db.commit()

        # Remove file from disk after successful DB delete
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as exc:
                logger.warning("Could not remove file %s: %s", file_path, exc)

        logger.info("Deleted document %s", document_id)
