"""Document processing tasks — PDF parsing, chunking, vectorization, AI analysis."""

import asyncio
import logging
import re
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


# ── TOC Extraction ─────────────────────────────────────


def _extract_pdf_bookmarks_sync(file_path: str, total_pages: int) -> list[dict]:
    """Extract sections from PDF bookmark / outline tree (sync).

    Returns list of {title, start_page, end_page, from_bookmark} dicts,
    sorted by start_page. Returns [] on failure or empty outline.
    """
    try:
        import pypdf  # pdfplumber ships pypdf as a dependency
    except ImportError:
        return []

    try:
        reader = pypdf.PdfReader(file_path)
        outline = reader.outline
        if not outline:
            return []

        flat: list[dict] = []

        def _traverse(items: list, level: int = 0) -> None:
            for item in items:
                if isinstance(item, list):
                    _traverse(item, level + 1)
                elif hasattr(item, "title"):
                    try:
                        page_num = reader.get_destination_page_number(item) + 1  # 1-indexed
                        title = (item.title or "").strip()
                        if title and page_num >= 1:
                            flat.append(
                                {"title": title, "start_page": page_num, "level": level}
                            )
                    except Exception:
                        pass

        _traverse(outline)
        if not flat:
            return []

        # Sort by page number, deduplicate identical pages (keep first)
        flat.sort(key=lambda s: s["start_page"])
        seen_pages: set[int] = set()
        unique: list[dict] = []
        for entry in flat:
            if entry["start_page"] not in seen_pages:
                seen_pages.add(entry["start_page"])
                unique.append(entry)

        # Only keep top-level (level 0) or level 1 entries if there are too many
        top_entries = [e for e in unique if e["level"] == 0]
        if not top_entries:
            top_entries = unique

        # Compute end_page
        result: list[dict] = []
        for i, sec in enumerate(top_entries):
            end_page = top_entries[i + 1]["start_page"] - 1 if i + 1 < len(top_entries) else total_pages
            if end_page < sec["start_page"]:
                end_page = total_pages
            result.append(
                {
                    "title": sec["title"],
                    "start_page": sec["start_page"],
                    "end_page": end_page,
                    "from_bookmark": True,
                }
            )
        return result
    except Exception:
        logger.exception("Failed to extract PDF bookmarks from %s", file_path)
        return []


# TOC text-line pattern: optional leading number, title, optional dots/spaces, page number
_TOC_LINE_RE = re.compile(
    r"^(?:(?:[0-9]+[\.\-]?)+\s+)?(.{3,80}?)\s*[\.·•\-]{0,15}\s*(\d{1,4})\s*$"
)
_TOC_KEYWORDS = {"table of contents", "contents", "index", "目录", "índice"}


def _scan_text_for_toc(pages: list[dict]) -> list[dict]:
    """Scan first ~10 pages for a TOC page and parse entries.

    Returns list of {title, start_page, end_page} dicts, or [].
    """
    toc_entries: list[tuple[str, int]] = []  # (title, page_number)

    for page_data in pages[:10]:
        text = page_data.get("text", "") or ""
        if not text.strip():
            continue

        # Check if this page looks like a TOC page
        lower = text.lower()
        if not any(kw in lower for kw in _TOC_KEYWORDS):
            continue

        # Parse TOC lines
        matches: list[tuple[str, int]] = []
        for line in text.splitlines():
            line = line.strip()
            m = _TOC_LINE_RE.match(line)
            if m:
                title = m.group(1).strip(" .")
                pg = int(m.group(2))
                if title and 1 <= pg <= 2000 and len(title) >= 3:
                    matches.append((title, pg))

        if len(matches) >= 3:
            toc_entries = matches
            break

    if not toc_entries:
        return []

    total_pages = len(pages)
    result: list[dict] = []
    for i, (title, start_page) in enumerate(toc_entries):
        if start_page > total_pages:
            continue
        end_page = toc_entries[i + 1][1] - 1 if i + 1 < len(toc_entries) else total_pages
        end_page = max(start_page, min(end_page, total_pages))
        result.append(
            {
                "title": title,
                "start_page": start_page,
                "end_page": end_page,
                "from_bookmark": False,
            }
        )
    return result


async def _extract_toc_from_pdf(file_path: str, pages: list[dict]) -> list[dict]:
    """Extract table of contents from a PDF (async wrapper).

    Tries PDF bookmarks first, then text-based TOC scan.
    Returns list of {title, start_page, end_page, from_bookmark} dicts.
    Empty list → caller should fall back to page-group sectioning.
    """
    toc = await asyncio.to_thread(_extract_pdf_bookmarks_sync, file_path, len(pages))
    if toc:
        logger.info("Extracted %d TOC sections from PDF bookmarks", len(toc))
        return toc

    toc = _scan_text_for_toc(pages)
    if toc:
        logger.info("Extracted %d TOC sections from text scan", len(toc))
        return toc

    logger.info("No TOC found in PDF; will fall back to page-group sections")
    return []


def _build_sections_from_toc(
    toc: list[dict], pages: list[dict], document_id: object
) -> list[tuple]:
    """Create BidDocumentSection ORM objects from extracted TOC entries.

    Returns list of (section_orm, content_str) tuples ready to add to the session.
    """
    sections_and_content: list[tuple] = []
    for item in toc:
        start_p = item["start_page"]
        end_p = item["end_page"]
        section_pages = [p for p in pages if start_p <= p["page_number"] <= end_p]
        content = "\n\n".join(
            f"=== 第{p['page_number']}页 ===\n{p['text']}"
            for p in section_pages
            if p["text"].strip()
        )
        section = BidDocumentSection(
            bid_document_id=document_id,
            section_type="toc_section",
            section_title=item["title"],
            start_page=start_p,
            end_page=end_p,
            content_preview=content[:500],
            detected_by="bookmark" if item.get("from_bookmark") else "toc_scan",
        )
        sections_and_content.append((section, content))
    return sections_and_content


def _build_page_group_sections(
    pages: list[dict], document_id: object, group_size: int = 5
) -> list[tuple]:
    """Fall-back: split pages into fixed-size groups as BidDocumentSection objects."""
    sections_and_content: list[tuple] = []
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
            bid_document_id=document_id,
            section_type="full_document",
            section_title=f"第{page_group[0]['page_number']}-{page_group[-1]['page_number']}页",
            start_page=page_group[0]["page_number"],
            end_page=page_group[-1]["page_number"],
            content_preview=content[:500],
        )
        sections_and_content.append((section, content))
    return sections_and_content


async def _generate_ai_analysis(sample_text: str) -> tuple[str, str]:
    """Call LLM to generate a structured Markdown overview for a single document.

    Returns (overview_markdown, ""). Falls back to empty strings on failure.
    """
    from app.agents.llm_client import LLMClient, Message

    client = LLMClient()
    clipped = sample_text[:8000]

    system_prompt = (
        "你是一名专业的多边开发银行（ADB/WB/AfDB）招标文件分析师。\n"
        "请仔细阅读提供的招标文件内容，生成结构化的文档解读报告。\n"
        "严格按照以下五个章节输出，使用 Markdown 格式（## 作为章节标题），不要输出 JSON：\n\n"
        "## 一、项目概览\n"
        "（100-150字）项目名称、所在国家/地区、建设目标与背景。\n\n"
        "## 二、核心技术要求\n"
        "（150-200字）主要技术范围、核心系统/设备、交付要求与技术规范重点。\n\n"
        "## 三、投标人资质要求\n"
        "（100-150字）资质标准、关键人员要求、必要的业绩或认证要求。\n\n"
        "## 四、关键时间节点\n"
        "（100字以内）投标文件发布日期、截止日期、评标计划等关键时间点。\n\n"
        "## 五、阅读重点与注意事项\n"
        "（150-200字）文档阅读顺序建议、需特别关注的条款、常见误解与风险提示。\n\n"
        "仅输出以上五个章节的 Markdown 内容，不要有任何额外说明或前言。"
    )

    try:
        response = await client.chat(
            messages=[
                Message("system", system_prompt),
                Message("user", f"以下是招标文件的部分内容：\n\n{clipped}"),
            ],
            temperature=0.3,
            max_tokens=2500,
        )
        overview = response.content.strip()
        return overview, ""
    except Exception:
        logger.exception("AI analysis generation failed")
        return "", ""


async def _analyze_document_from_db(document_id: str) -> dict:
    """Re-analyze an existing document: regenerate sections (if needed) and generate AI overview."""
    async with async_session() as db:
        result = await db.execute(
            select(BidDocument).where(BidDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        # Re-parse PDF to get text
        pages = await _parse_pdf(doc.file_path)
        if not pages:
            logger.warning("No pages for document %s — cannot generate AI overview", document_id)
            return {"status": "error", "reason": "no_content"}

        # Regenerate sections if all existing sections are plain page groups
        existing_result = await db.execute(
            select(BidDocumentSection).where(BidDocumentSection.bid_document_id == document_id)
        )
        existing_sections = existing_result.scalars().all()
        all_page_groups = all(s.section_type == "full_document" for s in existing_sections)

        if all_page_groups:
            logger.info(
                "Document %s has only page-group sections — attempting TOC extraction",
                document_id,
            )
            toc_items = await _extract_toc_from_pdf(doc.file_path, pages)
            if toc_items:
                # Delete old page-group sections and replace with TOC sections
                for sec in existing_sections:
                    await db.delete(sec)
                await db.flush()
                toc_section_tuples = _build_sections_from_toc(toc_items, pages, document_id)
                for section, _content in toc_section_tuples:
                    db.add(section)
                logger.info(
                    "Replaced %d page-group sections with %d TOC sections for document %s",
                    len(existing_sections),
                    len(toc_section_tuples),
                    document_id,
                )

        sample_text = "\n\n".join(
            p["text"] for p in pages[:30] if p["text"].strip()
        )

        overview, reading_tips = await _generate_ai_analysis(sample_text)
        doc.ai_overview = overview or None
        doc.ai_reading_tips = reading_tips or None
        await db.commit()

        logger.info("AI analysis generated for document %s", document_id)
        return {"status": "ok", "document_id": document_id}


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

            # 4. Create sections — try PDF TOC first, fallback to page groups
            toc_items = await _extract_toc_from_pdf(doc.file_path, pages)
            if toc_items:
                section_tuples = _build_sections_from_toc(toc_items, pages, doc.id)
            else:
                section_tuples = _build_page_group_sections(pages, doc.id)
            for section, _content in section_tuples:
                db.add(section)

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
            doc.processing_progress = 85
            await db.commit()

            # 7. Generate AI overview and reading tips
            sample_text = "\n\n".join(
                p["text"] for p in pages[:30] if p["text"].strip()
            )
            overview, reading_tips = await _generate_ai_analysis(sample_text)
            doc.ai_overview = overview or None
            doc.ai_reading_tips = reading_tips or None
            doc.processing_progress = 95
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


async def _generate_combined_ai_analysis(project_id: str) -> dict:
    """Merge all processed documents' text and generate one unified overview for the project."""
    from app.models.project import Project

    async with async_session() as db:
        proj_result = await db.execute(select(Project).where(Project.id == project_id))
        project = proj_result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        doc_result = await db.execute(
            select(BidDocument).where(
                BidDocument.project_id == project_id,
                BidDocument.status.in_(["processed", "completed"]),
            )
        )
        docs = doc_result.scalars().all()
        if not docs:
            logger.warning("No processed documents for project %s — skipping combined analysis", project_id)
            return {"status": "no_content"}

        # Collect sample text from each document (up to 6000 chars each, 12000 total)
        parts: list[str] = []
        per_doc_limit = max(2000, 12000 // len(docs))
        for doc in docs:
            pages = await _parse_pdf(doc.file_path)
            if not pages:
                continue
            text = "\n\n".join(p["text"] for p in pages[:30] if p["text"].strip())
            label = doc.original_filename or doc.filename
            parts.append(f"【{label}】\n{text[:per_doc_limit]}")

        if not parts:
            return {"status": "no_content"}

        combined_text = "\n\n---\n\n".join(parts)

        from app.agents.llm_client import LLMClient, Message
        client = LLMClient()

        system_prompt = (
            "你是一名专业的多边开发银行（ADB/WB/AfDB）招标文件分析师。\n"
            "以下提供了同一项目的多个招标文件（可能分为不同卷册，如技术卷、商务卷、图纸卷等），"
            "请将它们作为一个完整的招标项目综合分析，生成统一的解读报告，不要按文件分开描述。\n"
            "严格按照以下五个章节输出，使用 Markdown 格式（## 作为章节标题），不要输出 JSON：\n\n"
            "## 一、项目概览\n"
            "（150-200字）项目名称、所在国家/地区、建设目标与背景、资金来源（如 ADB/WB/AfDB）。\n\n"
            "## 二、核心技术要求\n"
            "（200-250字）主要技术范围、核心系统/设备、交付要求与技术规范重点；如有多个卷册，说明各自技术侧重。\n\n"
            "## 三、投标人资质要求\n"
            "（150-200字）资质标准、关键人员与专家要求、必要的业绩或认证要求。\n\n"
            "## 四、关键时间节点\n"
            "（100字以内）投标文件发布日期、截止日期、评标计划、合同签署预期等关键时间点。\n\n"
            "## 五、阅读重点与注意事项\n"
            "（200-250字）各卷册间的关系与推荐阅读顺序、需特别关注的条款（如 BDS/SCC/EQC）、"
            "常见误解与风险提示、投标人行动建议。\n\n"
            "仅输出以上五个章节的 Markdown 内容，不要有任何额外说明或前言。"
        )

        try:
            response = await client.chat(
                messages=[
                    Message("system", system_prompt),
                    Message("user", f"以下是同一招标项目的多个招标文件内容（可能为不同卷册）：\n\n{combined_text[:12000]}"),
                ],
                temperature=0.3,
                max_tokens=3000,
            )
            overview = response.content.strip()
        except Exception:
            logger.exception("Combined AI analysis failed for project %s", project_id)
            return {"status": "error"}

        project.combined_ai_overview = overview or None
        project.combined_ai_reading_tips = None
        await db.commit()

        logger.info("Combined AI analysis generated for project %s", project_id)
        return {"status": "ok", "project_id": project_id}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def generate_combined_document_ai(self, project_id: str) -> dict:
    """Generate a unified AI overview across all processed documents of a project."""
    logger.info("Generating combined AI analysis for project %s", project_id)
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _generate_combined_ai_analysis(project_id)
        )
        logger.info("Combined AI analysis done for project %s: %s", project_id, result)
        return result
    except Exception as exc:
        logger.exception("Combined AI analysis failed for project %s", project_id)
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def generate_document_ai(self, document_id: str) -> dict:
    """Generate (or regenerate) AI overview and reading tips for an existing document.

    Safe to call on already-processed documents that lack ai_overview.
    """
    logger.info("Generating AI analysis for document %s", document_id)
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _analyze_document_from_db(document_id)
        )
        logger.info("AI analysis done for document %s: %s", document_id, result)
        return result
    except Exception as exc:
        logger.exception("AI analysis failed for document %s", document_id)
        raise self.retry(exc=exc) from exc
