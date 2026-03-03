"""Bid document service — upload, parse, search, manage bid documents."""

import hashlib
import logging
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.bid_document import BidDocument, BidDocumentSection

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
            .where(BidDocumentSection.document_id == document_id)
            .order_by(BidDocumentSection.order_index)
        )
        return list(result.scalars().all())

    async def delete(self, document_id: UUID) -> None:
        """Delete a document and remove its file from disk."""
        doc = await self.get_by_id(document_id)

        # Remove file
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        await self.db.delete(doc)
        await self.db.commit()
        logger.info("Deleted document %s", document_id)
