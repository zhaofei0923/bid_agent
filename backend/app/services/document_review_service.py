"""Document review service — per-checklist-item AI review against tender requirements."""

import asyncio
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_client import get_llm_client
from app.agents.mcp.bid_document_search import keyword_search_chunks
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """你是一位专业的多边发展银行投标顾问，负责审查用户提交的标书内容。

请根据以下信息进行审查：
1. 招标文件相关条款（RAG检索结果）
2. 需要编写的清单项目要求
3. 用户提交的内容

评分标准：
- 90-100：完全满足要求，内容充实
- 70-89：基本满足，有轻微不足
- 50-69：部分满足，需要改进
- 0-49：未满足主要要求

请仅输出 JSON。"""

REVIEW_PROMPT_TEMPLATE = """## 投标文件审查任务

**清单项目：** {item_title}

**项目编写要求：**
{item_guidance}

**招标文件相关条款：**
{doc_context}

**用户提交的内容：**
{user_content}

请审查用户提交内容是否满足招标要求，返回如下 JSON：
{{
  "score": <0-100整数>,
  "meets_requirements": <true/false>,
  "gaps": ["缺失或不足之处1", "缺失或不足之处2"],
  "suggestions": ["具体改进建议1", "具体改进建议2"],
  "knowledge_tips": ["相关知识要点1", "相关知识要点2"]
}}"""


class DocumentReviewService:
    """Per-checklist-item document review service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def review_item(
        self,
        project_id: UUID,
        item_title: str,
        item_guidance: str | None,
        source_section: str | None,
        source_excerpt: str | None,
        content_text: str | None,
        file_bytes: bytes | None,
        file_content_type: str | None,
    ) -> dict[str, Any]:
        """Review a single checklist item's drafted content.

        Handles:
        - Text paste: use content_text directly
        - Image upload (image/*): OCR via Tencent Cloud
        - PDF upload: extract text via pdfplumber

        Returns a dict with score, meets_requirements, gaps, suggestions, knowledge_tips.
        """
        # 1. Extract text from file if provided
        extracted_text: str = ""
        if file_bytes and file_content_type:
            extracted_text = await self._extract_file_text(
                file_bytes, file_content_type
            )

        user_content = content_text or extracted_text
        if not user_content or not user_content.strip():
            return {
                "success": False,
                "error": "未提供审查内容",
                "data": None,
                "tokens_consumed": 0,
            }

        # 2. RAG: search tender document for relevant chunks
        keywords: list[str] = _build_keywords(item_title, source_section, source_excerpt)
        chunks = await keyword_search_chunks(
            self.db, str(project_id), keywords, top_k=6
        )
        doc_context = _format_chunks(chunks)

        # 3. Build prompt
        prompt = REVIEW_PROMPT_TEMPLATE.format(
            item_title=item_title,
            item_guidance=item_guidance or "（无具体编写指导）",
            doc_context=doc_context or "（未找到相关招标文件条款）",
            user_content=user_content[:3000],  # cap to avoid token overflow
        )

        # 4. LLM review
        llm = get_llm_client()
        result = await llm.extract_json(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2000,
        )

        data = result.data
        if data.get("parse_error"):
            return {
                "success": False,
                "error": "AI 返回格式异常，请重试",
                "data": None,
                "tokens_consumed": result.tokens_used,
            }

        return {
            "success": True,
            "data": {
                "score": int(data.get("score", 0)),
                "meets_requirements": bool(data.get("meets_requirements", False)),
                "gaps": data.get("gaps", []),
                "suggestions": data.get("suggestions", []),
                "knowledge_tips": data.get("knowledge_tips", []),
            },
            "tokens_consumed": result.tokens_used,
        }

    async def _extract_file_text(
        self, file_bytes: bytes, content_type: str
    ) -> str:
        """Extract text from uploaded file (image or PDF)."""
        if content_type.startswith("image/"):
            return await self._ocr_image(file_bytes)
        elif content_type == "application/pdf":
            return await asyncio.to_thread(self._extract_pdf_text, file_bytes)
        return ""

    async def _ocr_image(self, image_bytes: bytes) -> str:
        """OCR image bytes using Tencent Cloud if enabled, else return empty."""
        if not getattr(settings, "TENCENT_OCR_ENABLED", False):
            logger.warning("Tencent OCR is disabled; cannot process image upload")
            return ""
        try:
            from app.services.document_processing.tencent_doc_parser import (
                TencentDocParser,
            )

            parser = TencentDocParser()
            text = await parser._call_ocr_api(image_bytes)
            return text
        except Exception:
            logger.warning("Tencent OCR failed for uploaded image", exc_info=True)
            return ""

    @staticmethod
    def _extract_pdf_text(file_bytes: bytes) -> str:
        """Extract text from first 3 pages of a PDF (sync, runs in thread pool)."""
        try:
            import io

            import pdfplumber

            parts: list[str] = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages[:3]:
                    text = page.extract_text() or ""
                    if text.strip():
                        parts.append(text.strip())
            return "\n\n".join(parts)
        except Exception:
            logger.warning("pdfplumber extraction failed", exc_info=True)
            return ""


# ── Helpers ─────────────────────────────────────────────────────────


def _build_keywords(
    item_title: str,
    source_section: str | None,
    source_excerpt: str | None,
) -> list[str]:
    """Build keyword list for tender document search."""
    import re

    raw = f"{item_title} {source_section or ''} {source_excerpt or ''}"
    # Extract Chinese phrases (2+ chars) and English words (3+ chars)
    zh = re.findall(r"[\u4e00-\u9fff]{2,}", raw)
    en = re.findall(r"[a-zA-Z]{3,}", raw)
    seen: set[str] = set()
    result: list[str] = []
    for kw in zh + en:
        k = kw.lower()
        if k not in seen:
            seen.add(k)
            result.append(kw)
    return result[:20]


def _format_chunks(chunks: list[dict]) -> str:
    """Format RAG chunks into a readable context string."""
    if not chunks:
        return ""
    parts: list[str] = []
    for i, chunk in enumerate(chunks[:5], 1):
        content = chunk.get("content", "").strip()
        if content:
            parts.append(f"[片段{i}] {content[:500]}")
    return "\n\n".join(parts)
