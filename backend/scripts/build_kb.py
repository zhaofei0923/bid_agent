"""
Phase 6: Knowledge Base Builder Script
Crawls ADB, World Bank, and AfDB procurement/guidelines pages,
downloads key PDF documents, parses them with pdfplumber, embeds
the text chunks with the ResilientEmbeddingClient, and inserts
everything into the knowledge_bases / knowledge_documents /
knowledge_chunks tables (with pgvector).

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/build_kb.py --source adb --limit 20
    python scripts/build_kb.py --source worldbank --limit 20
    python scripts/build_kb.py --source afdb --limit 20
    python scripts/build_kb.py --source all
"""

import argparse
import asyncio
import hashlib
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pdfplumber
from bs4 import BeautifulSoup
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Adjust import path so we can import app modules when running from scripts/
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.agents.embedding_client import get_embedding_client  # noqa: E402
from app.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Source catalogue  (url, title, category)
# ---------------------------------------------------------------------------

ADB_DOCUMENTS = [
    (
        "https://www.adb.org/sites/default/files/procurement/27431/procurement-regulations.pdf",
        "ADB Procurement Regulations for ADB Borrowers",
        "procurement_regulations",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement/27432/staff-instructions-procurement.pdf",
        "ADB Staff Instructions — Procurement",
        "staff_instructions",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement/27433/consulting-guidelines.pdf",
        "ADB Guidelines on the Use of Consultants",
        "consulting_guidelines",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement/485577/adb-sbd-consulting-firm.pdf",
        "ADB Standard Bidding Document — Consultant Services (Firm)",
        "sbd",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement/485583/adb-sbd-individual-consultant.pdf",
        "ADB Standard Bidding Document — Individual Consultant",
        "sbd",
    ),
]

WORLDBANK_DOCUMENTS = [
    (
        "https://thedocs.worldbank.org/en/doc/a5a4ddca47d3d269ece2a1ce5e1b02ed-0290032021/related/ProcurementRegulations07-2016revised07-2019-ES.pdf",
        "World Bank Procurement Regulations for IPF Borrowers",
        "procurement_regulations",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/6f49ee6c71954d5a14f22e7a0fbdab16-0290032021/related/StandardConsultingServicesSelection-Individual-English.pdf",
        "WB Standard Procurement Document — Selection of Individual Consultants",
        "sbd",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/7db7dbaaad96fd5e7e60cac0a31f83ce-0290032021/related/StandardConsultingServicesSelection-Firms-English.pdf",
        "WB Standard Procurement Document — Selection of Consulting Firms",
        "sbd",
    ),
]

AFDB_DOCUMENTS = [
    (
        "https://www.afdb.org/fileadmin/uploads/afdb/Documents/Generic-Documents/Rules_and_Procedures_for_the_Use_of_Consultants.pdf",
        "AfDB Rules and Procedures for the Use of Consultants",
        "consulting_guidelines",
    ),
    (
        "https://www.afdb.org/fileadmin/uploads/afdb/Documents/Procurement/Bidding-Documents/Standard-Request-for-Proposals-Consulting-Services.pdf",
        "AfDB Standard Request for Proposals — Consulting Services",
        "sbd",
    ),
]

SOURCE_MAP: dict[str, list[tuple[str, str, str]]] = {
    "adb": ADB_DOCUMENTS,
    "worldbank": WORLDBANK_DOCUMENTS,
    "afdb": AFDB_DOCUMENTS,
}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def get_session() -> AsyncSession:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return factory()


async def upsert_kb(session: AsyncSession, source: str) -> str:
    """Return existing KB id for source, or create a new one."""
    row = await session.execute(
        text("SELECT id FROM knowledge_bases WHERE source_name = :s LIMIT 1"),
        {"s": source},
    )
    existing = row.scalar_one_or_none()
    if existing:
        return str(existing)
    kb_id = str(uuid4())
    await session.execute(
        text(
            "INSERT INTO knowledge_bases (id, name, source_name, description, is_active, created_at, updated_at) "
            "VALUES (:id, :name, :sn, :desc, true, NOW(), NOW())"
        ),
        {
            "id": kb_id,
            "name": f"{source.upper()} Knowledge Base",
            "sn": source,
            "desc": f"Procurement guidelines and SBDs from {source.upper()}",
        },
    )
    await session.commit()
    return kb_id


async def doc_exists(session: AsyncSession, url: str) -> bool:
    row = await session.execute(
        text("SELECT 1 FROM knowledge_documents WHERE source_url = :u LIMIT 1"),
        {"u": url},
    )
    return row.scalar_one_or_none() is not None


async def insert_doc(
    session: AsyncSession,
    kb_id: str,
    title: str,
    url: str,
    category: str,
    file_path: str,
) -> str:
    doc_id = str(uuid4())
    await session.execute(
        text(
            "INSERT INTO knowledge_documents "
            "(id, knowledge_base_id, title, source_url, doc_type, file_path, status, created_at, updated_at) "
            "VALUES (:id, :kb, :title, :url, :dtype, :fp, 'processed', NOW(), NOW())"
        ),
        {
            "id": doc_id,
            "kb": kb_id,
            "title": title,
            "url": url,
            "dtype": category,
            "fp": file_path,
        },
    )
    await session.commit()
    return doc_id


async def insert_chunks(
    session: AsyncSession,
    doc_id: str,
    kb_id: str,
    chunks: list[dict[str, Any]],
) -> None:
    """Batch-insert knowledge_chunks with embeddings."""
    for chunk in chunks:
        await session.execute(
            text(
                "INSERT INTO knowledge_chunks "
                "(id, knowledge_document_id, knowledge_base_id, content, chunk_index, "
                " page_number, embedding, created_at) "
                "VALUES (:id, :doc, :kb, :content, :idx, :page, :emb::vector, NOW())"
            ),
            {
                "id": str(uuid4()),
                "doc": doc_id,
                "kb": kb_id,
                "content": chunk["content"],
                "idx": chunk["index"],
                "page": chunk.get("page"),
                "emb": str(chunk["embedding"]),
            },
        )
    await session.commit()


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------


def parse_pdf(path: str) -> list[dict[str, Any]]:
    """Return list of {page, text} dicts."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            try:
                t = page.extract_text() or ""
                if t.strip():
                    pages.append({"page": i, "text": t})
            except Exception as exc:  # noqa: BLE001
                log.warning("page %d extraction failed: %s", i, exc)
    return pages


def chunk_pages(pages: list[dict[str, Any]], chunk_size: int = 5) -> list[dict[str, Any]]:
    """Group pages into chunks of *chunk_size* pages."""
    chunks = []
    for i in range(0, len(pages), chunk_size):
        group = pages[i : i + chunk_size]
        text = "\n\n".join(p["text"] for p in group)
        chunks.append(
            {
                "index": i // chunk_size,
                "page": group[0]["page"],
                "content": text[:4000],  # cap at 4k chars
            }
        )
    return chunks


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------


async def download_pdf(url: str, dest: str) -> bool:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; BidAgentBot/2.0; "
            "+https://github.com/zhaofei0923/bid_agent)"
        )
    }
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=120, headers=headers
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            Path(dest).write_bytes(resp.content)
            return True
    except Exception as exc:  # noqa: BLE001
        log.error("download failed %s: %s", url, exc)
        return False


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------


async def process_document(
    session: AsyncSession,
    kb_id: str,
    url: str,
    title: str,
    category: str,
    emb_client: Any,
) -> None:
    if await doc_exists(session, url):
        log.info("  SKIP (already in DB): %s", title)
        return

    log.info("  Downloading: %s", url)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    ok = await download_pdf(url, tmp_path)
    if not ok:
        return

    try:
        pages = parse_pdf(tmp_path)
        if not pages:
            log.warning("  No text extracted from %s", title)
            return

        chunks = chunk_pages(pages)
        log.info("  Parsed %d pages → %d chunks", len(pages), len(chunks))

        # Vectorize in batch
        texts = [c["content"] for c in chunks]
        emb_results = await emb_client.embed_texts(texts)
        for i, emb in enumerate(emb_results):
            chunks[i]["embedding"] = emb.embedding

        doc_id = await insert_doc(session, kb_id, title, url, category, tmp_path)
        await insert_chunks(session, doc_id, kb_id, chunks)
        log.info("  ✓ Inserted doc %s with %d chunks", doc_id, len(chunks))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def run(source: str, limit: int) -> None:
    if source == "all":
        sources = list(SOURCE_MAP.keys())
    else:
        sources = [source]

    session = await get_session()
    emb_client = get_embedding_client()

    try:
        for src in sources:
            docs = SOURCE_MAP.get(src, [])
            if limit:
                docs = docs[:limit]
            log.info("=== Processing %d docs for source: %s ===", len(docs), src)
            kb_id = await upsert_kb(session, src)
            for url, title, category in docs:
                await process_document(session, kb_id, url, title, category, emb_client)
    finally:
        await session.close()

    log.info("Done.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Build knowledge base from MDB procurement docs")
    parser.add_argument(
        "--source",
        choices=["adb", "worldbank", "afdb", "all"],
        default="all",
        help="Which source to crawl (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max docs to process per source (0 = unlimited)",
    )
    args = parser.parse_args()
    asyncio.run(run(args.source, args.limit))


if __name__ == "__main__":
    main()
