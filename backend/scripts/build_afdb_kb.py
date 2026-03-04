"""
AfDB Knowledge Base Builder
从 AfDB 官网下载采购政策 PDF 并入库（使用 wget 绕过 WAF）

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/build_afdb_kb.py
"""

import asyncio
import contextlib
import hashlib
import logging
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import pdfplumber
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.agents.embedding_client import get_embedding_client  # noqa: E402
from app.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

WGET_HEADERS = [
    "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "--referer=https://www.afdb.org/en/projects-and-operations/procurement/new-procurement-policy",
]

# AfDB 采购框架核心文档
# 注：fileadmin/ 路径文件受 WAF 限制无法下载，仅保留 sites/default/files/ 路径
AFDB_DOCUMENTS = [
    # ── 业务采购手册 OPM（2025 年 4 月修订版）──────────────────────
    (
        "https://www.afdb.org/sites/default/files/2025/05/20/opm-part_a-volume_1-en_rev_apr_2025.pdf",
        "AfDB Operations Procurement Manual — Part A, Volume 1: General Considerations (Rev. April 2025)",
        "procurement_guidance",
    ),
    (
        "https://www.afdb.org/sites/default/files/2025/05/20/opm-part_a-volume_2-en_rev_apr_2025.pdf",
        "AfDB Operations Procurement Manual — Part A, Volume 2: Specialized Procurement (Rev. April 2025)",
        "procurement_guidance",
    ),
    (
        "https://www.afdb.org/sites/default/files/2025/05/20/opm-part_a-volume_3-en_rev_apr_2025.pdf",
        "AfDB Operations Procurement Manual — Part A, Volume 3: Annexes (Rev. April 2025)",
        "procurement_guidance",
    ),
    (
        "https://www.afdb.org/sites/default/files/2025/05/20/opm-part_b-en_rev_apr_2025.pdf",
        "AfDB Operations Procurement Manual — Part B: Roles & Responsibilities of the Bank & Borrower (Rev. April 2025)",
        "procurement_guidance",
    ),
    # ── 仲裁中心评估报告 ────────────────────────────────────────────
    (
        "https://www.afdb.org/sites/default/files/2023/01/24/2014_report_arbitration_centres_ccja_crcica_and_lcia-miac_published.pdf",
        "AfDB 2014 Assessment Report on Arbitration Centres (CCJA, CRCICA, LCIA-MIAC)",
        "procurement_guidance",
    ),
    (
        "https://www.afdb.org/sites/default/files/2023/01/24/2022_report_on_arbitration_centre_crcica_published.pdf",
        "AfDB 2022 Assessment Report on Arbitration Centre CRCICA (Egypt)",
        "procurement_guidance",
    ),
]


# ---------------------------------------------------------------------------
# wget 下载（绕过 WAF）
# ---------------------------------------------------------------------------

def wget_download(url: str, dest_path: str, retries: int = 3) -> bool:
    """使用 wget 下载文件，自动重试，返回是否成功。"""
    for attempt in range(1, retries + 1):
        # 每次重试前随机等待，避免被 WAF 限速
        if attempt > 1:
            wait = random.uniform(8, 15)
            log.info("    Retry %d/%d, waiting %.1fs...", attempt, retries, wait)
            time.sleep(wait)
        cmd = ["wget", "-nv", "-O", dest_path, "--timeout=60", "--tries=1", *WGET_HEADERS, url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.warning("    wget exit %d: %s", result.returncode, result.stderr[:120].strip())
            continue
        if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 1000:
            log.warning("    File too small or missing")
            continue
        # 检查是否真的是 PDF（防止下载了 HTML 错误页面）
        with open(dest_path, "rb") as f:
            magic = f.read(4)
        if magic == b"%PDF":
            return True
        log.warning("    Not a valid PDF (magic: %s)", magic)
    return False


# ---------------------------------------------------------------------------
# PDF 解析
# ---------------------------------------------------------------------------

def parse_pdf(path: str) -> list[dict[str, Any]]:
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            try:
                t = page.extract_text() or ""
                if t.strip():
                    pages.append({"page": i, "text": t})
            except Exception as exc:
                log.warning("page %d extraction failed: %s", i, exc)
    return pages


def chunk_pages(pages: list[dict[str, Any]], chunk_size: int = 5) -> list[dict[str, Any]]:
    chunks = []
    for i in range(0, len(pages), chunk_size):
        group = pages[i : i + chunk_size]
        text = "\n\n".join(p["text"] for p in group)
        chunks.append({"index": i // chunk_size, "page": group[0]["page"], "content": text})
    return chunks


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def get_session() -> AsyncSession:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return factory()


async def upsert_kb(session: AsyncSession) -> str:
    row = await session.execute(
        text("SELECT id FROM knowledge_bases WHERE institution = 'afdb' AND kb_type = 'procurement' LIMIT 1")
    )
    existing = row.scalar_one_or_none()
    if existing:
        return str(existing)
    kb_id = str(uuid4())
    await session.execute(
        text(
            "INSERT INTO knowledge_bases (id, name, institution, kb_type, description, created_at, updated_at) "
            "VALUES (:id, 'AfDB Knowledge Base', 'afdb', 'procurement', "
            "'Procurement policies, guidelines and SBDs from African Development Bank', NOW(), NOW())"
        ),
        {"id": kb_id},
    )
    await session.commit()
    return kb_id


async def doc_exists(session: AsyncSession, url: str) -> bool:
    url_hash = hashlib.md5(url.encode()).hexdigest()
    row = await session.execute(
        text("SELECT 1 FROM knowledge_documents WHERE file_hash = :h LIMIT 1"),
        {"h": url_hash},
    )
    return row.scalar_one_or_none() is not None


async def insert_doc(session: AsyncSession, kb_id: str, title: str, url: str, file_path: str) -> str:
    doc_id = str(uuid4())
    url_hash = hashlib.md5(url.encode()).hexdigest()
    await session.execute(
        text(
            "INSERT INTO knowledge_documents "
            "(id, knowledge_base_id, filename, file_path, file_hash, status, created_at, updated_at) "
            "VALUES (:id, :kb, :filename, :fp, :fhash, 'processed', NOW(), NOW())"
        ),
        {"id": doc_id, "kb": kb_id, "filename": title[:255], "fp": file_path, "fhash": url_hash},
    )
    await session.commit()
    return doc_id


async def insert_chunks(session: AsyncSession, doc_id: str, chunks: list[dict[str, Any]]) -> None:
    for chunk in chunks:
        await session.execute(
            text(
                "INSERT INTO knowledge_chunks "
                "(id, document_id, content, chunk_index, page_number, embedding, created_at) "
                "VALUES (:id, :doc, :content, :idx, :page, CAST(:emb AS vector), NOW())"
            ),
            {
                "id": str(uuid4()),
                "doc": doc_id,
                "content": chunk["content"],
                "idx": chunk["index"],
                "page": chunk.get("page"),
                "emb": str(chunk["embedding"]),
            },
        )
    await session.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run() -> None:
    session = await get_session()
    emb_client = get_embedding_client()
    kb_id = await upsert_kb(session)
    log.info("AfDB KB id: %s", kb_id)
    log.info("Processing %d documents", len(AFDB_DOCUMENTS))

    ok_count = 0
    skip_count = 0
    fail_count = 0

    for url, title, _category in AFDB_DOCUMENTS:
        # 检查是否已入库
        if await doc_exists(session, url):
            log.info("  SKIP (already in DB): %s", title)
            skip_count += 1
            continue

        log.info("  Downloading: %s", url)
        # 随机等待 3-8 秒，避免触发 Cloudflare 速率限制
        delay = random.uniform(3, 8)
        log.info("  Waiting %.1fs before download...", delay)
        time.sleep(delay)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tmp_path = tf.name

        try:
            success = wget_download(url, tmp_path)
            if not success:
                log.error("  ✗ Download failed or not a valid PDF: %s", url)
                fail_count += 1
                continue

            size_kb = os.path.getsize(tmp_path) // 1024
            log.info("  Downloaded %.0f KB, parsing PDF...", size_kb)

            pages = parse_pdf(tmp_path)
            if not pages:
                log.warning("  ✗ No text extracted from PDF: %s", title)
                fail_count += 1
                continue

            chunks = chunk_pages(pages)
            log.info("  Parsed %d pages → %d chunks", len(pages), len(chunks))

            # 向量化
            texts = [c["content"] for c in chunks]
            emb_results = await emb_client.embed_texts(texts)
            for i, emb in enumerate(emb_results):
                chunks[i]["embedding"] = emb.embedding

            # 入库
            doc_id = await insert_doc(session, kb_id, title, url, tmp_path)
            await insert_chunks(session, doc_id, chunks)
            log.info("  ✓ Inserted doc %s with %d chunks [model: %s]", doc_id, len(chunks), emb_results[0].model)
            ok_count += 1

        except Exception as exc:
            log.exception("  ✗ Error processing %s: %s", title, exc)
            fail_count += 1
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)

    log.info("\n=== Done ===")
    log.info("Success: %d | Skipped: %d | Failed: %d", ok_count, skip_count, fail_count)

    # 统计入库情况
    row = await session.execute(
        text(
            "SELECT COUNT(DISTINCT d.id), COUNT(c.id) "
            "FROM knowledge_bases kb "
            "JOIN knowledge_documents d ON d.knowledge_base_id = kb.id "
            "JOIN knowledge_chunks c ON c.document_id = d.id "
            "WHERE kb.institution = 'afdb'"
        )
    )
    docs, chunks = row.one()
    log.info("AfDB KB total: %d docs, %d chunks in database", docs, chunks)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
