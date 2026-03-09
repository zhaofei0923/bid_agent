"""Bid document parser — identifies ADB/WB standard sections in parsed PDFs."""

import logging
import re

logger = logging.getLogger(__name__)

# ── Section patterns covering ADB and WB Standard Bidding Documents ──────────
#
# Each entry tries multiple patterns: Markdown headings (from pymupdf4llm),
# plain text section headers, and abbreviation-only matches.
# Patterns are ordered from most specific to least specific to reduce
# false-positive matches (e.g. "ITB" alone can appear in many contexts,
# so we prefer "Section 1: Instructions to Bidders" first).

SECTION_PATTERNS = [
    {
        "type": "section_1_itb",
        "title": "Section 1: Instructions to Bidders",
        "patterns": [
            r"(?im)^#{1,3}\s*section\s*1[:\.\s]+instruction",
            r"(?i)section\s*1[:\.\s]+instruction\s*to\s*bidder",
            r"(?i)instructions?\s*to\s*bidders?\s*\(?\s*ITB\s*\)?",
        ],
    },
    {
        "type": "section_2_bds",
        "title": "Section 2: Bid Data Sheet",
        "patterns": [
            r"(?im)^#{1,3}\s*section\s*2[:\.\s]+bid\s*data",
            r"(?i)section\s*2[:\.\s]+bid\s*data\s*sheet",
            r"(?i)bid\s*data\s*sheet\s*\(?\s*BDS\s*\)?",
        ],
    },
    {
        "type": "section_3_qualification",
        "title": "Section 3: Evaluation and Qualification Criteria",
        "patterns": [
            r"(?im)^#{1,3}\s*section\s*3[:\.\s]+(evaluation|qualification)",
            r"(?i)section\s*3[:\.\s]+(evaluation|qualification)",
            r"(?i)evaluation\s*(and|&)\s*qualification\s*criteria",
        ],
    },
    {
        "type": "section_4_forms",
        "title": "Section 4: Bidding Forms",
        "patterns": [
            r"(?im)^#{1,3}\s*section\s*4[:\.\s]+bidding\s*form",
            r"(?i)section\s*4[:\.\s]+bidding\s*form",
            r"(?i)section\s*(IV|4)[:\.\s]+(?:standard\s+)?(?:bidding|procurement)\s*form",
        ],
    },
    {
        "type": "section_5_tos",
        "title": "Section 5: Eligible Countries / Terms of Reference",
        "patterns": [
            r"(?im)^#{1,3}\s*section\s*5",
            r"(?i)section\s*5[:\.\s]+eligible\s*countries",
            r"(?i)section\s*5[:\.\s]+terms?\s*of\s*reference",
        ],
    },
    {
        "type": "part_2_requirements",
        "title": "Part 2: Supply/Works Requirements",
        "patterns": [
            r"(?im)^#{1,3}\s*part\s*2[:\.\s]",
            r"(?i)part\s*(?:2|ii|two)[:\.\s]+(?:supply|works?)\s*requirement",
            r"(?i)(?:employer.?s|purchaser.?s)\s*requirements?",
            r"(?i)scope\s*of\s*(?:works?|supply)",
        ],
    },
    {
        "type": "part_3_contract",
        "title": "Part 3: Conditions of Contract",
        "patterns": [
            r"(?im)^#{1,3}\s*part\s*3[:\.\s]",
            r"(?i)part\s*(?:3|iii|three)[:\.\s]+condition",
            r"(?i)general\s*conditions?\s*of\s*contract",
        ],
    },
    # ── WB-specific patterns ──────────────────────────────
    {
        "type": "section_1_itb",
        "title": "Section I: Instructions to Bidders",
        "patterns": [
            r"(?i)section\s*I[:\.\s]+instruction\s*to\s*bidder",
        ],
    },
    {
        "type": "section_2_bds",
        "title": "Section II: Bid Data Sheet",
        "patterns": [
            r"(?i)section\s*II[:\.\s]+bid\s*data\s*sheet",
        ],
    },
    {
        "type": "section_3_qualification",
        "title": "Section III: Evaluation and Qualification Criteria",
        "patterns": [
            r"(?i)section\s*III[:\.\s]+(evaluation|qualification)",
        ],
    },
    {
        "type": "section_4_forms",
        "title": "Section IV: Bidding Forms",
        "patterns": [
            r"(?i)section\s*IV[:\.\s]+(?:bidding|procurement)\s*form",
        ],
    },
]


def identify_sections(
    text: str,
    page_texts: list[str] | None = None,
) -> list[dict]:
    """Identify standard bid document sections in parsed text.

    Scans full document text for ADB/WB standard section boundaries using
    regex patterns (including Markdown headings from pymupdf4llm).

    When the same section_type is matched by multiple pattern groups,
    only the first (earliest) match is kept.

    Args:
        text: Full document text (plain text or Markdown).
        page_texts: Optional per-page text list for page number mapping.

    Returns:
        List of identified sections with type, title, start/end positions,
        page numbers, and content. Sorted by document position.
    """
    # Collect first match per section_type
    best: dict[str, dict] = {}

    for section_def in SECTION_PATTERNS:
        stype = section_def["type"]
        if stype in best:
            continue  # already matched this section_type

        for pattern in section_def["patterns"]:
            match = re.search(pattern, text)
            if match:
                page_number = _find_page_number(match.start(), page_texts)
                best[stype] = {
                    "section_type": stype,
                    "title": section_def["title"],
                    "char_start": match.start(),
                    "page_number": page_number,
                }
                break  # first matching pattern per definition is enough

    sections = sorted(best.values(), key=lambda s: s["char_start"])

    # Compute content ranges
    for i, section in enumerate(sections):
        if i + 1 < len(sections):
            section["char_end"] = sections[i + 1]["char_start"]
        else:
            section["char_end"] = len(text)

        section["content"] = text[section["char_start"] : section["char_end"]]
        section["page_end"] = _find_page_number(section["char_end"], page_texts)

    logger.info("Identified %d sections in document", len(sections))
    return sections


def _find_page_number(
    char_offset: int,
    page_texts: list[str] | None,
) -> int:
    """Map a character offset to a 1-based page number."""
    if not page_texts:
        return 1

    current_offset = 0
    for i, page_text in enumerate(page_texts):
        current_offset += len(page_text)
        if current_offset >= char_offset:
            return i + 1

    return len(page_texts)
