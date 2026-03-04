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
import contextlib
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
from sqlalchemy import text
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
    # ── 核心政策与指令 (Core Policy & Directive) ────────────────────────────
    (
        "https://www.adb.org/sites/default/files/adb-procurement-policy.pdf",
        "ADB Procurement Policy — Goods, Works, Nonconsulting and Consulting Services (2017)",
        "procurement_regulations",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-directive-adb-borrowers.pdf",
        "ADB Procurement Directive for ADB Borrowers (Effective 1 January 2026)",
        "procurement_regulations",
    ),
    # ── 采购标准文件 — 咨询服务 (SBDs — Consulting Services) ──────────────────
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
    # ── 指导手册 — 准备与规划 (Guidance Notes — Preparation & Planning) ──────
    (
        "https://www.adb.org/sites/default/files/procurement-risk-framework.pdf",
        "ADB Procurement Risk Framework — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-planning.pdf",
        "ADB Strategic Procurement Planning — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-review.pdf",
        "ADB Procurement Review — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/alternative-procurement-arrangements.pdf",
        "ADB Alternative Procurement Arrangements — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/early-market-engagement-procurement-guidance-note.pdf",
        "ADB Early Market Engagement — Procurement Guidance Note",
        "procurement_guidance",
    ),
    # ── 指导手册 — 采购方法 (Guidance Notes — Procurement Methods) ────────────
    (
        "https://www.adb.org/sites/default/files/open-competitive-bidding.pdf",
        "ADB Open Competitive Bidding — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/consulting-services.pdf",
        "ADB Consulting Services Administered by ADB Borrowers — Guidance Note",
        "consulting_guidelines",
    ),
    (
        "https://www.adb.org/sites/default/files/nonconsulting-services.pdf",
        "ADB Nonconsulting Services Administered by ADB Borrowers — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/framework-agreements-consulting.pdf",
        "ADB Framework Agreements for Consulting Services — Guidance Note",
        "procurement_guidance",
    ),
    # ── 指导手册 — 投标程序 (Guidance Notes — Bidding Procedures) ─────────────
    (
        "https://www.adb.org/sites/default/files/procurement-price-adjustment.pdf",
        "ADB Price Adjustment — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-prequalification.pdf",
        "ADB Prequalification — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-subcontracting.pdf",
        "ADB Subcontracting — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-domestic-preference.pdf",
        "ADB Domestic Preference — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/bid-evaluation-procurement-guidance-note.pdf",
        "ADB Bid Evaluation — Procurement Guidance Note (January 2026)",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/merit-point-criteria-procurement-guidance-note.pdf",
        "ADB Merit Point Criteria — Procurement Guidance Note",
        "procurement_guidance",
    ),
    # ── 指导手册 — 原则与实践 (Guidance Notes — Principles & Practices) ────────
    (
        "https://www.adb.org/sites/default/files/procurement-value-money.pdf",
        "ADB Value for Money — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-quality.pdf",
        "ADB Quality — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/contract-management.pdf",
        "ADB Contract Management — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/abnormally-low-bids.pdf",
        "ADB Abnormally Low Bids — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/local-participation-procurement-guidance-note.pdf",
        "ADB Local Participation — Procurement Guidance Note",
        "procurement_guidance",
    ),
    # ── 指导手册 — 投诉、合规与资格 (Guidance Notes — Complaints & Compliance) ─
    (
        "https://www.adb.org/sites/default/files/bidding-related-complaints.pdf",
        "ADB Bidding-Related Complaints — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/noncompliance-procurement.pdf",
        "ADB Noncompliance in Procurement — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-standstill-period.pdf",
        "ADB Standstill Period — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/procurement-state-owned-enterprises.pdf",
        "ADB State-Owned Enterprises — Procurement Guidance Note",
        "procurement_guidance",
    ),
    # ── 指导手册 — 专项领域 (Guidance Notes — Specialized Areas) ──────────────
    (
        "https://www.adb.org/sites/default/files/procurement-fragile-situations.pdf",
        "ADB Fragile and Conflict-Affected Situations, SIDS, and Emergency Situations — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/eprocurement.pdf",
        "ADB E-Procurement — Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/ppp-procurement.pdf",
        "ADB Public–Private Partnerships — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/high-level-technology.pdf",
        "ADB High-Level Technology — Procurement Guidance Note",
        "procurement_guidance",
    ),
    (
        "https://www.adb.org/sites/default/files/sustainable-public-procurement.pdf",
        "ADB Sustainable Public Procurement — Guidance Note",
        "procurement_guidance",
    ),
]

WORLDBANK_DOCUMENTS = [
    # ── 核心强制性文件 (Mandatory Requirements) ──────────────────────────────
    (
        "https://thedocs.worldbank.org/en/doc/c84273d1b230aeb2b0b8134de5dc8cd7-0290012025/original/Procurement-Regulations-7th-Edition-Sep-2025.pdf",
        "WB Procurement Regulations for IPF Borrowers — 7th Edition (Sep 2025)",
        "procurement_regulations",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/02c022198520f5b6ab2ecfe64e56ec19-0290012023/original/Bank-Policy-Procurement-in-IPF-and-Other-Operational-Procurement-Matters.pdf",
        "WB Bank Policy — Procurement in IPF and Other Operational Procurement Matters",
        "procurement_regulations",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/2d4449540430ed046e159dc5d1ff45ed-0290012024/original/Procurement-Directive-April-2024.pdf",
        "WB Procurement Directive in IPF and Other Operational Procurement Matters (Apr 2024)",
        "procurement_regulations",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/6b5517ea27b46baf0e1328ba369ea214-0290012025/original/Bank-Procedure-Procurement-in-IPF-and-other-Operational-Procurement-Matters.pdf",
        "WB Bank Procedure — Procurement in IPF and Other Operational Procurement Matters (Sep 2025)",
        "procurement_regulations",
    ),
    # ── 标准采购文件 (Standard Procurement Documents — SPDs) ─────────────────
    (
        "https://thedocs.worldbank.org/en/doc/6f49ee6c71954d5a14f22e7a0fbdab16-0290032021/related/StandardConsultingServicesSelection-Individual-English.pdf",
        "WB SPD — Selection of Individual Consultants",
        "sbd",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/7db7dbaaad96fd5e7e60cac0a31f83ce-0290032021/related/StandardConsultingServicesSelection-Firms-English.pdf",
        "WB SPD — Selection of Consulting Firms (QCBS / QBS / FBS / LCS)",
        "sbd",
    ),
    # ── 采购入门指南 (Beginner Guides) ───────────────────────────────────────
    (
        "https://documents1.worldbank.org/curated/en/099825508192516096/pdf/IDU-89b91972-9bb3-4b74-8382-101e7bb13e95.pdf",
        "WB Beginner's Guide for Borrowers — Procurement under World Bank IPF",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099413404292517723/pdf/IDU-7301cb21-f811-432d-8bbc-33fd64040959.pdf",
        "WB Beginner's Guide for Suppliers — Finding Opportunities and Winning Contracts",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099133508192535977/pdf/IDU-585b8ced-fd94-490c-828b-34083b46f90f.pdf",
        "WB Beginner's Guide to Standard Procurement Documents (SPDs)",
        "procurement_guidance",
    ),
    # ── 阈值与采购策略 (Thresholds & Strategy) ───────────────────────────────
    (
        "https://thedocs.worldbank.org/en/doc/656a913f77e8ac21084b1fa2c4e3a5b1-0290012024/original/BG-TfP.pdf",
        "WB Thresholds for Procurement Approaches and Methods by Country",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099629208202516861/pdf/IDU-e2e57ebf-34aa-4499-9ed1-99d1b06fe315.pdf",
        "WB PPSD Guidance Long Form — Project Procurement Strategy for Development",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099637208202516621/pdf/IDU-bf05be13-141f-4672-8d9a-8ae750628a9f.pdf",
        "WB PPSD Guidance Short Form — Project Procurement Strategy for Development",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099646308202517077/pdf/IDU-b7e5df0d-12a7-4c11-a217-c46a3557aa2c.pdf",
        "WB PPSD Guidance Short Form (Chinese) — 项目采购策略指南（短表）",
        "procurement_guidance",
    ),
    # ── 采购发起与资格 (Initiating Procurement) ──────────────────────────────
    (
        "https://documents1.worldbank.org/curated/en/099557008202532821/pdf/IDU-b82f9f90-bf98-4c25-b6d4-929201de045b.pdf",
        "WB Conflict of Interest — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099133308192536038/pdf/IDU-2e6ac2e4-ae16-4622-ad51-8ef7f6afbc89.pdf",
        "WB Request for Expression of Interest (REoI) — Template and Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099710507092534067/pdf/IDU-2f5f55a5-f19b-41cb-bf5e-601fd69cce52.pdf",
        "WB How to Write Technical Specifications — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099803108202534425/pdf/IDU-54262265-fe12-4ae3-9fea-e82f800cec96.pdf",
        "WB Value for Money — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099606408202533891/pdf/IDU-af48d92a-b02c-431c-9354-5d4b82a8fb6f.pdf",
        "WB Early Market Engagement — Procurement Fact Sheet",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099616508202518912/pdf/IDU-7b275269-09c6-43cc-a853-a9313396325d.pdf",
        "WB Framework Agreements — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099228308192560599/pdf/IDU-c59e6c91-d2f6-4191-bd6b-ac99fc6a6182.pdf",
        "WB Aggregated Procurement — Fact Sheet",
        "procurement_guidance",
    ),
    # ── 评标与选择 (Evaluating and Selecting) ────────────────────────────────
    (
        "https://documents1.worldbank.org/curated/en/099325208202512194/pdf/IDU-a052dfd8-ab44-44c1-b854-870b4cccacdb.pdf",
        "WB Evaluating Bids and Proposals Using Rated Criteria — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099343408202523703/pdf/IDU-269b9721-a8ff-49b1-bf3d-d05e51bf69e1.pdf",
        "WB Evaluating Bids Using Rated Criteria (Chinese) — 使用评分标准评估投标",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099812008202522046/pdf/IDU-3d758f2f-9715-47ca-a1d8-79011ae808d9.pdf",
        "WB Abnormally Low Bids and Proposals — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099826508202525853/pdf/IDU-db90b397-d1d2-4c55-bfd2-473e10127c2f.pdf",
        "WB Competitive Dialogue — How to Undertake a Competitive Dialogue Procurement Process",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099217108262522575/pdf/IDU-d1454a14-b000-459d-a327-ae943ec3c3a9.pdf",
        "WB Negotiations and Best and Final Offer — Procurement Guidance",
        "procurement_guidance",
    ),
    # ── 合同实施 (Contract Implementation) ───────────────────────────────────
    (
        "https://documents1.worldbank.org/curated/en/099513208262519456/pdf/IDU-01fc74fa-175d-4707-a892-90ecc1b8167f.pdf",
        "WB Contract Management General Principles — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099812309012526724/pdf/IDU-f71614f0-c8a8-4150-9d74-a3bf98f6e52c.pdf",
        "WB Contract Management Practice — Procurement Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099539108262581005/pdf/IDU-90a965a9-13c9-4734-bae6-c72f71653e97.pdf",
        "WB Supply Chain Management — Procurement Guidance",
        "procurement_guidance",
    ),
    # ── 投诉与监督 (Complaints & Oversight) ──────────────────────────────────
    (
        "https://documents1.worldbank.org/curated/en/099149508192519086/pdf/IDU-5d2efb17-fc21-47f9-a7d1-08bcbd0b087b.pdf",
        "WB Procurement-Related Complaints — Procurement Guidance (English)",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099156108192528177/pdf/IDU-4648c799-e92a-43fd-a581-0bec98f7dc8b.pdf",
        "WB Procurement-Related Complaints — Procurement Guidance (Chinese 中文)",
        "procurement_guidance",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/b34ab66724064f5d88cf0381e1e11eae-0290012023/original/Bank-Guidance-Procurement-Post-Review-Independent-Procurement-Review-and-Integrated-Fiduciary-Reviews.pdf",
        "WB Bank Oversight — Post Review, Independent Procurement Review, and Integrated Fiduciary Reviews",
        "procurement_guidance",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/e75f33d5a27809c47675b20f41240334-0290012023/original/Bank-Guidance-Procurement-Noncompliance-in-IPF-Operations.pdf",
        "WB Noncompliance in IPF Operations — Bank Guidance",
        "procurement_guidance",
    ),
    # ── 紧急与特殊情形 (Specialized & Emergency) ─────────────────────────────
    (
        "https://thedocs.worldbank.org/en/doc/975d0cb5b71e5ce28bd65312c8066815-0290012023/original/Bank-Guidance-Procurement-in-Situations-of-Urgent-need-of-Assistance-or-Capacity-Constraints.pdf",
        "WB Situations of Urgent Need of Assistance or Capacity Constraints — Bank Guidance",
        "procurement_guidance",
    ),
    (
        "https://thedocs.worldbank.org/en/doc/a9d40aabedcd96ec86b8d7743a09a95d-0290012023/original/Bank-Guidance-Procurement-Hands-on-Expanded-Implementation-Support.pdf",
        "WB HEIS — Hands-on Expanded Implementation Support Bank Guidance",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099813310292526449/pdf/IDU-31c38df9-e9eb-44e2-aec9-e9e17fb0b826.pdf",
        "WB Health — Engaging an Expert Consultant for Medical Diagnostic Equipment",
        "procurement_guidance",
    ),
    (
        "https://documents1.worldbank.org/curated/en/099701110292529690/pdf/IDU-a0c2520e-f4ae-48f3-8dd1-19db2c7e658f.pdf",
        "WB Sexual Exploitation and Abuse and Sexual Harassment (SEA/SH) — Q&A for Procurement",
        "procurement_guidance",
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
        text("SELECT id FROM knowledge_bases WHERE institution = :s AND kb_type = 'procurement' LIMIT 1"),
        {"s": source},
    )
    existing = row.scalar_one_or_none()
    if existing:
        return str(existing)
    kb_id = str(uuid4())
    await session.execute(
        text(
            "INSERT INTO knowledge_bases (id, name, institution, kb_type, description, created_at, updated_at) "
            "VALUES (:id, :name, :inst, 'procurement', :desc, NOW(), NOW())"
        ),
        {
            "id": kb_id,
            "name": f"{source.upper()} Knowledge Base",
            "inst": source,
            "desc": f"Procurement guidelines and SBDs from {source.upper()}",
        },
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


async def insert_doc(
    session: AsyncSession,
    kb_id: str,
    title: str,
    url: str,
    category: str,
    file_path: str,
) -> str:
    doc_id = str(uuid4())
    url_hash = hashlib.md5(url.encode()).hexdigest()
    await session.execute(
        text(
            "INSERT INTO knowledge_documents "
            "(id, knowledge_base_id, filename, file_path, file_hash, status, created_at, updated_at) "
            "VALUES (:id, :kb, :filename, :fp, :fhash, 'processed', NOW(), NOW())"
        ),
        {
            "id": doc_id,
            "kb": kb_id,
            "filename": title[:255],
            "fp": file_path,
            "fhash": url_hash,
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
                "(id, document_id, content, chunk_index, "
                " page_number, embedding, created_at) "
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
            except Exception as exc:
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
    except Exception as exc:
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
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)


async def run(source: str, limit: int) -> None:
    sources = list(SOURCE_MAP.keys()) if source == "all" else [source]

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
