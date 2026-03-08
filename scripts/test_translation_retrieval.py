#!/usr/bin/env python3
"""测试脚本：对比中文直接检索 vs Hunyuan 翻译后英文检索的准确率差异。

用法：
    cd backend
    python ../scripts/test_translation_retrieval.py

依赖：
    - .env 文件中配置 DATABASE_URL, HUNYUAN_SECRET_ID, HUNYUAN_SECRET_KEY
    - 生产库中存在已处理完成的招标文件（bid_document_chunks with embeddings）
"""

import asyncio
import os
import sys

# 加入 backend 目录到 path（本地开发：scripts/../backend；容器内：/app）
_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.join(_script_dir, "..", "backend")
if os.path.isdir(_backend_dir):
    sys.path.insert(0, os.path.abspath(_backend_dir))
elif os.path.isdir("/app"):
    sys.path.insert(0, "/app")

from dotenv import load_dotenv

_env_file = os.path.join(_script_dir, "../backend/.env")
if os.path.isfile(_env_file):
    load_dotenv(_env_file)
elif os.path.isfile("/app/.env"):
    load_dotenv("/app/.env")

# ── 测试问题 ──────────────────────────────────────────────────────────────────
TEST_QUESTIONS = [
    "投标截止日期是什么时候？",
    "投标保证金是多少？需要什么格式？",
    "对投标人的资质要求有哪些？",
    "关键人员需要具备什么经验和资质？",
    "技术评分标准和权重是什么？",
]


async def translate_zh_to_en(text: str) -> str:
    """用 Hunyuan Chat API 将中文问题翻译为英文。"""
    from tencentcloud.common import credential
    from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

    from app.config import get_settings

    settings = get_settings()
    cred = credential.Credential(settings.HUNYUAN_SECRET_ID, settings.HUNYUAN_SECRET_KEY)
    client = hunyuan_client.HunyuanClient(cred, "")

    req = models.ChatCompletionsRequest()
    req.Model = "hunyuan-lite"
    msg = models.Message()
    msg.Role = "user"
    msg.Content = (
        "请将以下招标相关的中文问题精确翻译为英文，保留专业术语，只输出英文翻译，不要任何解释：\n\n"
        f"{text}"
    )
    req.Messages = [msg]
    req.Stream = False

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(None, client.ChatCompletions, req)
    return resp.Choices[0].Message.Content.strip()


async def vector_search(db, project_id: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """向量相似度检索。"""
    from sqlalchemy import text

    sql = text("""
        SELECT ch.content, ch.page_number,
               1 - (ch.embedding <=> cast(:embedding as vector)) AS similarity,
               COALESCE(s.section_title, '') AS section_title,
               d.filename AS filename
        FROM bid_document_chunks ch
        JOIN bid_documents d ON ch.bid_document_id = d.id
        LEFT JOIN bid_document_sections s ON ch.section_id = s.id
        WHERE d.project_id = :project_id
          AND d.status IN ('processed', 'completed')
          AND ch.embedding IS NOT NULL
        ORDER BY ch.embedding <=> cast(:embedding as vector)
        LIMIT :top_k
    """)
    result = await db.execute(sql, {
        "embedding": str(query_embedding),
        "project_id": project_id,
        "top_k": top_k,
    })
    rows = result.fetchall()
    return [{"content": r.content[:200], "page": r.page_number, "score": float(r.similarity), "section": r.section_title} for r in rows]


async def find_project(db, name_keyword: str) -> str | None:
    """按名称关键词查找项目 ID。"""
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT id, name FROM projects WHERE name ILIKE :kw LIMIT 1"),
        {"kw": f"%{name_keyword}%"},
    )
    row = result.fetchone()
    if row:
        print(f"📁 找到项目: {row.name} (id={row.id})")
        return str(row.id)
    return None


async def count_chunks(db, project_id: str) -> int:
    from sqlalchemy import text
    result = await db.execute(
        text("""
            SELECT COUNT(*) FROM bid_document_chunks ch
            JOIN bid_documents d ON ch.bid_document_id = d.id
            WHERE d.project_id = :pid AND ch.embedding IS NOT NULL
        """),
        {"pid": project_id},
    )
    return result.scalar_one()


async def main():
    print("=" * 70)
    print("🔬 招标文件检索准确率对比测试：中文 Query vs 英文翻译 Query")
    print("=" * 70)

    from app.agents.embedding_client import get_embedding_client
    from app.database import async_session

    embedding_client = get_embedding_client()

    async with async_session() as db:
        # 查找项目
        project_id = await find_project(db, "nepal") or await find_project(db, "尼泊尔")
        if not project_id:
            print("❌ 未找到 nepal/尼泊尔 项目，请先确保项目存在")
            return

        n_chunks = await count_chunks(db, project_id)
        if n_chunks == 0:
            print("❌ 该项目没有已向量化的 chunks，请先处理招标文件")
            return
        print(f"✅ 找到 {n_chunks} 个向量化 chunks\n")

        # 对每个问题做对比
        results = []
        for i, question in enumerate(TEST_QUESTIONS, 1):
            print(f"\n{'─' * 60}")
            print(f"问题 {i}: {question}")

            # --- 方式 A: 中文直接 embed ---
            emb_zh = await embedding_client.embed_text(question)
            chunks_zh = await vector_search(db, project_id, emb_zh.embedding)
            top_zh = chunks_zh[0] if chunks_zh else {}

            # --- 翻译 ---
            try:
                en_query = await translate_zh_to_en(question)
                print(f"   英文翻译: {en_query}")
            except Exception as e:
                print(f"   ⚠️ 翻译失败: {e}, 跳过英文检索")
                en_query = None

            # --- 方式 B: 英文 embed ---
            top_en = {}
            if en_query:
                emb_en = await embedding_client.embed_text(en_query)
                chunks_en = await vector_search(db, project_id, emb_en.embedding)
                top_en = chunks_en[0] if chunks_en else {}

            # 打印对比
            score_zh = top_zh.get("score", 0)
            score_en = top_en.get("score", 0)
            delta = score_en - score_zh
            delta_str = f"+{delta:.4f}" if delta > 0 else f"{delta:.4f}"
            improved = "✅ 提升" if delta > 0.01 else ("⚠️ 持平" if abs(delta) < 0.01 else "❌ 下降")

            print(f"\n   [A] 中文 Query  相似度: {score_zh:.4f}  | section: {top_zh.get('section','')[:40]}")
            print(f"       top chunk: {top_zh.get('content','')[:100]}...")
            print(f"\n   [B] 英文 Query  相似度: {score_en:.4f}  | section: {top_en.get('section','')[:40]}")
            print(f"       top chunk: {top_en.get('content','')[:100]}...")
            print(f"\n   📊 差值: {delta_str}  {improved}")

            results.append({
                "question": question,
                "en_query": en_query or "",
                "score_zh": score_zh,
                "score_en": score_en,
                "delta": delta,
            })

    # 汇总
    print(f"\n{'=' * 70}")
    print("📊 汇总报告")
    print(f"{'=' * 70}")
    print(f"{'问题':<20} {'中文得分':>8} {'英文得分':>8} {'差值':>8} {'结论'}")
    print(f"{'─' * 60}")
    total_delta = 0.0
    for r in results:
        delta = r["delta"]
        total_delta += delta
        conclusion = "✅" if delta > 0.01 else ("⚠️" if abs(delta) < 0.01 else "❌")
        print(f"{r['question'][:20]:<20} {r['score_zh']:>8.4f} {r['score_en']:>8.4f} {delta:>+8.4f}  {conclusion}")
    avg = total_delta / len(results) if results else 0
    print(f"{'─' * 60}")
    print(f"{'平均差值':<20} {'':>8} {'':>8} {avg:>+8.4f}")
    print()
    if avg > 0.02:
        print("🎉 结论：英文翻译 Query 显著提升检索准确率，建议实施翻译方案！")
    elif avg > 0:
        print("🟡 结论：英文翻译有轻微提升，可实施，但效益有限。")
    else:
        print("🔴 结论：翻译未带来明显提升，可能 embedding 模型已支持跨语言检索。")


if __name__ == "__main__":
    asyncio.run(main())
