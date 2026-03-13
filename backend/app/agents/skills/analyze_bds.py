"""AnalyzeBDS — analyze Bid Data Sheet modifications to standard provisions.

Uses a chunked multi-call strategy to avoid LLM timeout:
  1. Split the BDS context into manageable batches (~3000 chars each)
  2. Call LLM in parallel for each batch
  3. Aggregate all results and generate summary statistics
"""

import asyncio
import logging
import re

from app.agents.skills.base import Skill, SkillContext, SkillResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是专业的多边发展银行投标分析师，精通 ADB Standard Bidding Documents。"
    "请逐条分析 BDS (Bid Data Sheet) 对 ITB (Instructions to Bidders) "
    "标准条款的修改。对每一条 BDS 给出: ITB 原条款号 → 标准内容摘要 → "
    "BDS 修改内容 → 修改影响分析 → 投标人行动项。"
)

BATCH_PROMPT = """请逐条分析以下 BDS (Bid Data Sheet) 内容片段，对每条 BDS 引用的 ITB 标准条款进行对照解读。

=== BDS 内容片段 ===
{bid_chunk}

=== ITB 标准条款参考 (知识库) ===
{kb_context}

分析要求:
1. 对每一条 BDS 引用的 ITB 条款号，找出标准条款原文含义
2. 分析 BDS 对该标准条款做了什么修改或补充
3. 评估该修改对投标人的影响程度
4. 给出投标人需要采取的具体行动

请以 JSON 格式返回:
{{
  "bds_modifications": [
    {{
      "bds_reference": "BDS x",
      "itb_clause": "ITB x.x",
      "itb_standard_content": "ITB 标准条款原文摘要（如知识库中有则引用，否则标注'标准条款待核实'）",
      "bds_modification": "BDS 具体修改/补充内容",
      "change_type": "override|supplement|specify|restrict|waive",
      "priority": "critical|high|medium|low",
      "impact_analysis": "对投标人的影响详细说明",
      "action_required": "投标人需要采取的具体行动",
      "compliance_note": "合规注意事项"
    }}
  ]
}}
"""

# Max chars per batch sent to LLM — keeps each call fast
BATCH_CHAR_LIMIT = 3000


def _split_bds_into_batches(bid_context: str) -> list[str]:
    """Split BDS context into batches by source blocks.

    RAG context is formatted as blocks starting with ``[来源 N]``.
    We group consecutive blocks so each batch is under BATCH_CHAR_LIMIT.
    If no source markers exist, we fall back to splitting by double-newline.
    """
    # Split by "[来源 N]" source markers
    blocks = re.split(r"(?=\[来源 \d+\])", bid_context.strip())
    blocks = [b.strip() for b in blocks if b.strip()]

    if not blocks:
        return [bid_context] if bid_context.strip() else []

    batches: list[str] = []
    current_batch: list[str] = []
    current_len = 0

    for block in blocks:
        block_len = len(block)
        # If adding this block exceeds limit and we already have content,
        # flush current batch
        if current_len + block_len > BATCH_CHAR_LIMIT and current_batch:
            batches.append("\n\n".join(current_batch))
            current_batch = []
            current_len = 0
        current_batch.append(block)
        current_len += block_len

    if current_batch:
        batches.append("\n\n".join(current_batch))

    return batches


class AnalyzeBDS(Skill):
    """Analyze BDS modifications to standard ITB provisions."""

    name = "analyze_bds"
    description = "分析 BDS 对标准条款的修改及其对投标人的影响"

    async def execute(self, ctx: SkillContext) -> SkillResult:
        bid_context = ctx.parameters.get("bid_context", "")
        kb_context = ctx.parameters.get("kb_context", "")

        if not bid_context:
            return SkillResult(
                success=True,
                data={
                    "bds_modifications": [],
                    "critical_changes_summary": "未检索到 BDS 相关内容，可能文档中未包含 Bid Data Sheet 章节或文档解析未识别该章节。",
                    "compliance_checklist": [],
                    "statistics": {
                        "total_bds_items": 0,
                        "critical_count": 0,
                        "high_count": 0,
                        "medium_count": 0,
                        "low_count": 0,
                    },
                },
            )

        # Split into batches for parallel LLM calls
        batches = _split_bds_into_batches(bid_context)
        logger.info(
            "BDS analysis: %d chars split into %d batches",
            len(bid_context), len(batches),
        )

        # Process all batches in parallel
        all_modifications: list[dict] = []
        total_tokens = 0

        async def _analyze_batch(idx: int, chunk: str) -> tuple[list[dict], int]:
            """Analyze a single BDS batch."""
            prompt = BATCH_PROMPT.format(
                bid_chunk=chunk,
                kb_context=kb_context,
            )
            try:
                result = await ctx.llm_client.extract_json(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_tokens=4000,
                )
                mods = result.data.get("bds_modifications", [])
                logger.info("BDS batch %d/%d: %d items, %d tokens", idx + 1, len(batches), len(mods), result.tokens_used)
                return mods, result.tokens_used
            except Exception:
                logger.exception("BDS batch %d/%d failed", idx + 1, len(batches))
                return [], 0

        results = await asyncio.gather(
            *[_analyze_batch(i, b) for i, b in enumerate(batches)]
        )

        for mods, tokens in results:
            all_modifications.extend(mods)
            total_tokens += tokens

        # Deduplicate by bds_reference
        seen_refs: set[str] = set()
        unique_mods: list[dict] = []
        for mod in all_modifications:
            ref = mod.get("bds_reference", "")
            if ref and ref in seen_refs:
                continue
            if ref:
                seen_refs.add(ref)
            unique_mods.append(mod)

        # Build statistics
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for mod in unique_mods:
            p = mod.get("priority", "medium")
            if p in priority_counts:
                priority_counts[p] += 1

        # Build compliance checklist from critical/high items
        checklist = []
        for mod in unique_mods:
            if mod.get("priority") in ("critical", "high"):
                checklist.append({
                    "item": mod.get("action_required", mod.get("bds_modification", "")),
                    "bds_reference": f"{mod.get('bds_reference', '')} / {mod.get('itb_clause', '')}",
                    "status": "must_comply",
                    "difficulty": "challenging" if mod.get("priority") == "critical" else "moderate",
                })

        # Build critical changes summary
        critical_items = [
            m for m in unique_mods if m.get("priority") in ("critical", "high")
        ]
        summary_parts = [
            f"- {m.get('bds_reference', '?')}: {m.get('bds_modification', '')[:80]}"
            for m in critical_items[:10]
        ]
        critical_summary = "\n".join(summary_parts) if summary_parts else "无关键修改"

        logger.info(
            "BDS analysis complete: %d items (%d unique), %d tokens",
            len(all_modifications), len(unique_mods), total_tokens,
        )

        return SkillResult(
            success=True,
            data={
                "bds_modifications": unique_mods,
                "critical_changes_summary": critical_summary,
                "compliance_checklist": checklist,
                "statistics": {
                    "total_bds_items": len(unique_mods),
                    "critical_count": priority_counts["critical"],
                    "high_count": priority_counts["high"],
                    "medium_count": priority_counts["medium"],
                    "low_count": priority_counts["low"],
                },
            },
            tokens_consumed=total_tokens,
        )
