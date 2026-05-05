"""Bid document service — upload, parse, search, manage bid documents."""

import asyncio
import hashlib
import logging
import os
import re
from pathlib import Path
from uuid import UUID, uuid4

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
        uploaded_by: UUID | None = None,
    ) -> BidDocument:
        """Upload and register a bid document.

        File is saved to disk and a DB record created with status='pending'.
        The actual parsing + vectorization is handled by Celery tasks.
        """
        original_filename = Path(filename or "upload").name
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", original_filename).strip("._")
        safe_name = safe_name[:180] or "upload"
        suffix = Path(safe_name).suffix.lower()

        allowed_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if suffix not in allowed_types:
            raise ValidationError("Unsupported file type. Only PDF and DOCX are supported")
        if content_type and content_type not in {
            allowed_types[suffix],
            "application/octet-stream",
            "binary/octet-stream",
        }:
            raise ValidationError(f"Unsupported file type: {content_type}")
        if suffix == ".pdf" and not content.startswith(b"%PDF-"):
            raise ValidationError("Invalid PDF file")
        if suffix == ".docx" and not content.startswith(b"PK"):
            raise ValidationError("Invalid DOCX file")

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

        upload_root = Path(settings.UPLOAD_DIR).resolve()
        upload_dir = (upload_root / str(project_id)).resolve()
        if upload_root not in upload_dir.parents and upload_dir != upload_root:
            raise ValidationError("Invalid upload path")
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_filename = f"{uuid4().hex}{suffix}"
        file_path = (upload_dir / stored_filename).resolve()
        if upload_dir not in file_path.parents:
            raise ValidationError("Invalid upload filename")

        await asyncio.to_thread(file_path.write_bytes, content)

        # Create DB record
        doc = BidDocument(
            project_id=project_id,
            filename=stored_filename,
            original_filename=safe_name,
            file_path=str(file_path),
            file_size=len(content),
            file_hash=file_hash,
            status="pending",
            uploaded_by=uploaded_by,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        logger.info(
            "Uploaded document %s for project %s (%d bytes)",
            doc.id, project_id, len(content),
        )
        return doc

    async def get_by_id(
        self,
        document_id: UUID,
        project_id: UUID | None = None,
    ) -> BidDocument:
        """Get a document by ID."""
        stmt = select(BidDocument).where(BidDocument.id == document_id)
        if project_id is not None:
            stmt = stmt.where(BidDocument.project_id == project_id)
        result = await self.db.execute(stmt)
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

    async def delete(
        self,
        document_id: UUID,
        project_id: UUID | None = None,
    ) -> None:
        """Delete a document and remove its file from disk.

        Uses raw SQL DELETE to avoid ORM session conflicts caused by
        lazy="selectin" pre-loading child objects into the session.
        DB ON DELETE CASCADE handles sections/chunks automatically.
        """
        # Fetch file_path only — noload prevents selectin from loading sections
        stmt = (
            select(BidDocument)
            .where(BidDocument.id == document_id)
            .options(noload(BidDocument.sections), noload(BidDocument.chunks))
        )
        if project_id is not None:
            stmt = stmt.where(BidDocument.project_id == project_id)
        result = await self.db.execute(stmt)
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
