"""Bid document parser — identifies ADB/WB standard sections in parsed PDFs."""

import logging
import re

logger = logging.getLogger(__name__)

# ADB Standard Bidding Document section patterns
ADB_SECTION_PATTERNS = [
    {
        "type": "section_1_itb",
        "title": "Section 1: Instructions to Bidders",
        "patterns": [
            r"(?i)section\s*1[:\.\s]*instruction",
            r"(?i)instructions?\s*to\s*bidders?",
            r"(?i)ITB",
        ],
    },
    {
        "type": "section_2_bds",
        "title": "Section 2: Bid Data Sheet",
        "patterns": [
            r"(?i)section\s*2[:\.\s]*bid\s*data",
            r"(?i)bid\s*data\s*sheet",
            r"(?i)BDS",
        ],
    },
    {
        "type": "section_3",
        "title": "Section 3: Evaluation and Qualification Criteria",
        "patterns": [
            r"(?i)section\s*3[:\.\s]*(evaluation|qualification)",
            r"(?i)evaluation\s*(and|&)\s*qualification\s*criteria",
            r"(?i)evaluation\s*criteria",
        ],
    },
    {
        "type": "section_4_forms",
        "title": "Section 4: Bidding Forms",
        "patterns": [
            r"(?i)section\s*4[:\.\s]*bidding\s*form",
            r"(?i)bidding\s*forms?",
        ],
    },
    {
        "type": "section_5_tos",
        "title": "Section 5: Terms of Reference / Eligible Countries",
        "patterns": [
            r"(?i)section\s*5",
            r"(?i)terms?\s*of\s*reference",
            r"(?i)eligible\s*countries",
        ],
    },
    {
        "type": "part_2_requirements",
        "title": "Part 2: Supply Requirements / Works Requirements",
        "patterns": [
            r"(?i)part\s*2",
            r"(?i)supply\s*requirements?",
            r"(?i)works?\s*requirements?",
            r"(?i)scope\s*of\s*works?",
        ],
    },
    {
        "type": "part_3_contract",
        "title": "Part 3: Conditions of Contract and Contract Forms",
        "patterns": [
            r"(?i)part\s*3",
            r"(?i)conditions?\s*of\s*contract",
            r"(?i)contract\s*forms?",
            r"(?i)general\s*conditions",
        ],
    },
]


def identify_sections(
    text: str,
    page_texts: list[str] | None = None,
) -> list[dict]:
    """Identify standard bid document sections in parsed text.

    Args:
        text: Full document text.
        page_texts: Optional per-page text list for page number mapping.

    Returns:
        List of identified sections with type, title, start/end positions,
        and page numbers.
    """
    sections: list[dict] = []

    for section_def in ADB_SECTION_PATTERNS:
        for pattern in section_def["patterns"]:
            match = re.search(pattern, text)
            if match:
                # Find the page number if page_texts provided
                page_number = _find_page_number(match.start(), page_texts)

                sections.append(
                    {
                        "section_type": section_def["type"],
                        "title": section_def["title"],
                        "char_start": match.start(),
                        "page_number": page_number,
                    }
                )
                break  # first matching pattern per section is enough

    # Sort by position and compute ranges
    sections.sort(key=lambda s: s["char_start"])

    for i, section in enumerate(sections):
        if i + 1 < len(sections):
            section["char_end"] = sections[i + 1]["char_start"]
            section["content"] = text[section["char_start"] : section["char_end"]]
        else:
            section["char_end"] = len(text)
            section["content"] = text[section["char_start"] :]

        end_page = _find_page_number(section["char_end"], page_texts)
        section["page_end"] = end_page

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
