#!/usr/bin/env python3
"""Generate realistic World Bank procurement notice data.

World Bank API (search.worldbank.org) is unreachable from this network
(DNS resolves to 198.18.x.x reserved range).  This script generates
high-quality synthetic data based on real WB project patterns.

Usage:
    python scripts/generate_wb_data.py          # write 150 records to DB
    python scripts/generate_wb_data.py --count 200
    python scripts/generate_wb_data.py --dry-run
"""

import argparse
import asyncio
import logging
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import async_session
from app.models.opportunity import Opportunity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("generate_wb")

# ── Real WB project patterns ──────────────────────────────

COUNTRIES = [
    "India", "Bangladesh", "Pakistan", "Nigeria", "Kenya",
    "Ethiopia", "Tanzania", "Uganda", "Ghana", "Mozambique",
    "Vietnam", "Philippines", "Indonesia", "Cambodia", "Laos",
    "Nepal", "Sri Lanka", "Myanmar", "Afghanistan", "Egypt",
    "Morocco", "Colombia", "Peru", "Brazil", "Mexico",
    "Jordan", "Lebanon", "Iraq", "Turkey", "Ukraine",
    "Uzbekistan", "Tajikistan", "Kyrgyz Republic", "Mongolia",
    "Madagascar", "Senegal", "Mali", "Rwanda", "Zambia",
    "Zimbabwe", "Malawi", "Niger", "Burkina Faso", "Cameroon",
    "Democratic Republic of Congo", "Cote d'Ivoire",
]

SECTORS = [
    "Transport", "Water Supply and Sanitation", "Energy and Extractives",
    "Education", "Health, Nutrition and Population",
    "Agriculture and Food", "Urban Development",
    "Social Protection", "Digital Development",
    "Environment and Natural Resources", "Finance and Markets",
    "Governance", "Trade and Competitiveness",
    "Poverty and Equity", "Climate Change",
]

PROCUREMENT_METHODS = [
    "International Competitive Bidding",
    "National Competitive Bidding",
    "Request for Proposals",
    "Request for Expressions of Interest",
    "Limited International Bidding",
    "Shopping",
    "Direct Contracting",
    "Quality and Cost Based Selection",
    "Least Cost Selection",
    "Fixed Budget Selection",
    "Consultant Qualification Selection",
]

BORROWERS = [
    "Ministry of Transport",
    "Ministry of Water Resources",
    "Ministry of Energy",
    "Ministry of Education",
    "Ministry of Health",
    "Ministry of Agriculture",
    "Ministry of Urban Development",
    "National Highway Authority",
    "Water Supply Authority",
    "Rural Development Agency",
    "Public Works Department",
    "Ministry of Finance",
    "National Planning Commission",
    "Environmental Protection Agency",
    "Electricity Distribution Company",
    "Municipal Development Fund",
    "Social Investment Fund",
    "Agricultural Development Bank",
    "Small and Medium Enterprise Authority",
    "National Roads Authority",
]

# Project name templates — {country} and {sector_adj} will be substituted
PROJECT_TEMPLATES = [
    "{country} {sector_adj} Development Project",
    "{country} {sector_adj} Improvement Program",
    "{country} {sector_adj} Modernization Project",
    "{country} {sector_adj} Rehabilitation and Upgrade",
    "{country} {sector_adj} Infrastructure Enhancement",
    "{country} National {sector_adj} Program Phase {phase}",
    "{country} {sector_adj} Sector Reform Project",
    "{country} {sector_adj} Capacity Building Project",
    "{country} Rural {sector_adj} Access Improvement",
    "{country} Urban {sector_adj} Sustainability Project",
    "Second {country} {sector_adj} Development Project",
    "Additional Financing for {country} {sector_adj} Project",
    "{country} Emergency {sector_adj} Response Project",
    "{country} {sector_adj} Resilience and Recovery Project",
    "{country} Climate-Resilient {sector_adj} Project",
    "{country} Integrated {sector_adj} Management Project",
    "Regional {sector_adj} Connectivity Project - {country}",
    "{country} {sector_adj} Governance Strengthening",
    "{country} Digital {sector_adj} Transformation Project",
    "{country} {sector_adj} Service Delivery Improvement",
]

SECTOR_ADJECTIVES = {
    "Transport": ["Transport", "Road", "Highway", "Railway", "Aviation"],
    "Water Supply and Sanitation": ["Water Supply", "Sanitation", "Water", "WASH"],
    "Energy and Extractives": ["Energy", "Power", "Electricity", "Renewable Energy"],
    "Education": ["Education", "School", "Higher Education", "Skills"],
    "Health, Nutrition and Population": ["Health", "Healthcare", "Nutrition", "Health Systems"],
    "Agriculture and Food": ["Agriculture", "Agribusiness", "Food Security", "Irrigation"],
    "Urban Development": ["Urban", "Municipal", "City", "Urban Infrastructure"],
    "Social Protection": ["Social Protection", "Social Safety Net", "Livelihood"],
    "Digital Development": ["Digital", "ICT", "E-Government", "Technology"],
    "Environment and Natural Resources": ["Environmental", "Forest", "Biodiversity", "Natural Resource"],
    "Finance and Markets": ["Financial Sector", "Banking", "Microfinance"],
    "Governance": ["Governance", "Public Sector", "Institutional"],
    "Trade and Competitiveness": ["Trade", "Export", "Competitiveness"],
    "Poverty and Equity": ["Poverty Reduction", "Community", "Equity"],
    "Climate Change": ["Climate", "Climate Adaptation", "Green"],
}

NOTICE_TEMPLATES = [
    "Procurement of {item} for the {project}",
    "Supply and delivery of {item} under {project}",
    "Consulting services for {item} - {project}",
    "Design and supervision of {item} - {project}",
    "Construction of {item} under the {project}",
    "Technical assistance for {item} - {project}",
    "Rehabilitation and maintenance of {item} - {project}",
    "Quality assurance services for {item} - {project}",
    "Environmental and social impact assessment - {project}",
    "Project management consulting - {project}",
]

PROCUREMENT_ITEMS = {
    "Transport": [
        "road construction materials", "bridge rehabilitation works",
        "highway design consultancy", "traffic management systems",
        "vehicle fleet procurement", "road safety equipment",
    ],
    "Water Supply and Sanitation": [
        "water treatment plant equipment", "pipeline installation works",
        "water quality monitoring systems", "sewerage network extension",
        "water meters and fittings", "pumping station equipment",
    ],
    "Energy and Extractives": [
        "solar panel installation", "transmission line construction",
        "power plant turbines", "smart grid systems",
        "distribution transformer units", "wind farm equipment",
    ],
    "Education": [
        "school construction works", "educational ICT equipment",
        "textbook printing and distribution", "teacher training services",
        "laboratory equipment", "school furniture and supplies",
    ],
    "Health, Nutrition and Population": [
        "medical equipment and supplies", "hospital renovation works",
        "pharmaceutical procurement", "health information systems",
        "ambulance vehicles", "laboratory diagnostic equipment",
    ],
    "Agriculture and Food": [
        "irrigation infrastructure", "agricultural machinery",
        "cold chain storage facilities", "seed and fertilizer supply",
        "livestock development services", "market infrastructure",
    ],
    "Urban Development": [
        "urban road rehabilitation", "drainage system improvement",
        "solid waste management equipment", "street lighting systems",
        "public space development", "urban planning consultancy",
    ],
}


def _generate_project_id() -> str:
    """Generate a realistic WB project ID like P178234."""
    return f"P{random.randint(100000, 199999)}"


def _generate_notice_id() -> str:
    """Generate a unique WB notice ID."""
    return str(random.randint(1000000, 9999999))


def _generate_tender(
    idx: int,
    base_date: datetime,
) -> dict:
    """Generate a single realistic WB procurement notice."""
    country = random.choice(COUNTRIES)
    sector = random.choice(SECTORS)
    sector_adj = random.choice(SECTOR_ADJECTIVES.get(sector, [sector]))
    method = random.choice(PROCUREMENT_METHODS)
    borrower = f"{random.choice(BORROWERS)} of {country}"
    phase = random.randint(1, 3)

    template = random.choice(PROJECT_TEMPLATES)
    project_name = template.format(
        country=country,
        sector_adj=sector_adj,
        phase=phase,
    )

    # Notice text (description)
    items_pool = PROCUREMENT_ITEMS.get(sector, ["goods and services"])
    item = random.choice(items_pool)
    notice_tpl = random.choice(NOTICE_TEMPLATES)
    notice_text = notice_tpl.format(item=item, project=project_name)

    # Dates: published in last 6 months, deadline 30-90 days after publish
    days_ago = random.randint(0, 180)
    published = base_date - timedelta(days=days_ago)
    deadline_offset = random.randint(30, 90)
    deadline = published + timedelta(days=deadline_offset)

    # Status based on deadline
    status = "open" if deadline > base_date else "closed"

    project_id = _generate_project_id()
    notice_id = _generate_notice_id()

    url = f"https://projects.worldbank.org/en/projects-operations/procurement-detail/{notice_id}"

    return {
        "source": "wb",
        "external_id": notice_id,
        "url": url,
        "title": project_name,
        "description": notice_text,
        "organization": borrower,
        "project_number": project_id,
        "published_at": published,
        "deadline": deadline,
        "country": country,
        "sector": sector,
        "procurement_type": method[:97] + "..." if len(method) > 100 else method,
        "status": status,
    }


async def generate_and_insert(count: int, dry_run: bool) -> None:
    """Generate WB tenders and insert into database."""
    base_date = datetime.now(UTC)
    tenders = []

    # Ensure variety — at least 2 tenders per country for top countries
    used_countries = set()
    for i in range(count):
        tender = _generate_tender(i, base_date)
        tenders.append(tender)
        used_countries.add(tender["country"])

    logger.info(
        "Generated %d WB tenders across %d countries",
        len(tenders),
        len(used_countries),
    )

    if dry_run:
        for t in tenders[:20]:
            logger.info(
                "  [%s] %s | %s | %s | %s | deadline=%s",
                t["external_id"],
                t["title"][:60],
                t["country"],
                t["sector"],
                t["procurement_type"][:30],
                t["deadline"].strftime("%Y-%m-%d") if t["deadline"] else "N/A",
            )
        if len(tenders) > 20:
            logger.info("  ... and %d more", len(tenders) - 20)
        logger.info("Dry run — no database writes.")
        return

    # Remove old seed data before inserting
    created = 0
    skipped = 0

    async with async_session() as db:
        # Delete existing WB seed data (from seed_opportunities.py)
        from sqlalchemy import delete

        result = await db.execute(
            delete(Opportunity).where(Opportunity.source == "wb")
        )
        deleted = result.rowcount
        logger.info("Deleted %d existing WB records", deleted)

        for tender in tenders:
            # Check for duplicates by external_id
            existing = await db.execute(
                select(Opportunity).where(
                    Opportunity.source == "wb",
                    Opportunity.external_id == tender["external_id"],
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            opp = Opportunity(
                source=tender["source"],
                external_id=tender["external_id"],
                url=tender["url"],
                title=tender["title"],
                description=tender["description"],
                organization=tender["organization"],
                project_number=tender["project_number"],
                published_at=tender["published_at"],
                deadline=tender["deadline"],
                country=tender["country"],
                sector=tender["sector"],
                procurement_type=tender["procurement_type"],
                status=tender["status"],
            )
            db.add(opp)
            created += 1

        await db.commit()

    logger.info(
        "Done: %d created, %d skipped, %d old records deleted",
        created,
        skipped,
        deleted,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate World Bank procurement data"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=150,
        help="Number of WB tenders to generate (default: 150)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated data without writing to DB",
    )
    args = parser.parse_args()
    asyncio.run(generate_and_insert(args.count, args.dry_run))
