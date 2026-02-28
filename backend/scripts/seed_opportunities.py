#!/usr/bin/env python3
"""Seed the opportunities table with sample ADB and WB tender data.

Usage:
    python scripts/seed_opportunities.py          # insert seeds
    python scripts/seed_opportunities.py --clear   # clear + re-seed
"""

import argparse
import asyncio
import logging
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select

from app.database import async_session
from app.models.opportunity import Opportunity

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger("seed")

NOW = datetime.now(UTC)


def _dt(days_ago: int) -> datetime:
    return NOW - timedelta(days=days_ago)


def _deadline(days_ahead: int) -> datetime:
    return NOW + timedelta(days=days_ahead)


# ── ADB Seed Data ────────────────────────────────────────────

ADB_SEEDS = [
    {
        "external_id": "1126376",
        "url": "https://www.adb.org/node/1126376",
        "title": "Loan 4426-UZB: Rural Roads Resilience Sector Project - Civil works",
        "description": "Civil works for the rehabilitation and performance-based maintenance services of Rural Roads in Khorezm Region (Lots 1, 2 & 3).",
        "organization": "Ministry of Transport, Uzbekistan",
        "project_number": "57004-001",
        "country": "Uzbekistan",
        "sector": "Transport",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(3),
        "deadline": _deadline(35),
    },
    {
        "external_id": "1126446",
        "url": "https://www.adb.org/node/1126446",
        "title": "South Asia Subregional Economic Cooperation Electricity Transmission Project (Package P-13)",
        "description": "Supply and installation of transmission lines and substation equipment for cross-border electricity exchange.",
        "organization": "Nepal Electricity Authority",
        "project_number": "54053-001",
        "country": "Nepal",
        "sector": "Energy",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(3),
        "deadline": _deadline(48),
    },
    {
        "external_id": "1125371",
        "url": "https://www.adb.org/node/1125371",
        "title": "Integrated Perinatal Care Project — Medical Equipment Package 1",
        "description": "Procurement of medical equipment for perinatal care centers in 5 regions of Uzbekistan.",
        "organization": "Ministry of Health, Uzbekistan",
        "project_number": "52340-001",
        "country": "Uzbekistan",
        "sector": "Health",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(6),
        "deadline": _deadline(40),
    },
    {
        "external_id": "1124950",
        "url": "https://www.adb.org/node/1124950",
        "title": "Punjab Intermediate Cities Improvement Investment Program - Water Supply",
        "description": "Construction of water supply network and treatment plant in Sargodha, Pakistan.",
        "organization": "Punjab Water & Sanitation Authority",
        "project_number": "48456-002",
        "country": "Pakistan",
        "sector": "Water and Urban Infrastructure",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(10),
        "deadline": _deadline(25),
    },
    {
        "external_id": "1124800",
        "url": "https://www.adb.org/node/1124800",
        "title": "Climate Resilient Rice Value Chain Development - Agricultural Advisory Services",
        "description": "Individual consulting services for climate-resilient rice production advisory program in Cambodia.",
        "organization": "Ministry of Agriculture, Cambodia",
        "project_number": "55120-001",
        "country": "Cambodia",
        "sector": "Agriculture and Food Security",
        "procurement_type": "Individual Consulting",
        "published_at": _dt(12),
        "deadline": _deadline(20),
    },
    {
        "external_id": "1124650",
        "url": "https://www.adb.org/node/1124650",
        "title": "Maharashtra Urban Transport Infrastructure Program - BRT Corridor",
        "description": "Design and construction of Bus Rapid Transit corridor in Nashik, India including stations and depots.",
        "organization": "Maharashtra Urban Transport Corporation",
        "project_number": "50334-003",
        "country": "India",
        "sector": "Transport",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(15),
        "deadline": _deadline(45),
    },
    {
        "external_id": "1124500",
        "url": "https://www.adb.org/node/1124500",
        "title": "Dhaka Mass Rapid Transit Development Project Line 1 - Rolling Stock",
        "description": "Supply of electric multiple unit (EMU) trains for MRT Line 1 in Dhaka, Bangladesh.",
        "organization": "Dhaka Mass Transit Company Limited",
        "project_number": "52093-001",
        "country": "Bangladesh",
        "sector": "Transport",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(18),
        "deadline": _deadline(60),
        "budget_min": 500000000,
        "budget_max": 800000000,
    },
    {
        "external_id": "1124350",
        "url": "https://www.adb.org/node/1124350",
        "title": "Georgia: Modernization of Water Supply Systems in Kutaisi",
        "description": "Rehabilitation and expansion of water supply and sewerage networks in Kutaisi, Georgia.",
        "organization": "Georgian Water and Power",
        "project_number": "56321-001",
        "country": "Georgia",
        "sector": "Water and Urban Infrastructure",
        "procurement_type": "General Procurement Notice",
        "published_at": _dt(20),
        "deadline": _deadline(30),
    },
    {
        "external_id": "1124200",
        "url": "https://www.adb.org/node/1124200",
        "title": "Digital Health Innovation and Data Analytics Consulting",
        "description": "Consulting services for design and implementation of digital health platform using AI-based diagnostics for rural health centers.",
        "organization": "ADB Knowledge Department",
        "project_number": "55678-001",
        "country": "Regional",
        "sector": "Health",
        "procurement_type": "Individual Consulting",
        "published_at": _dt(22),
        "deadline": _deadline(15),
    },
    {
        "external_id": "1124050",
        "url": "https://www.adb.org/node/1124050",
        "title": "Mongolia: Green Energy District Heating Conversion Program",
        "description": "Supply and installation of heat pump systems and solar thermal panels for district heating in Ulaanbaatar.",
        "organization": "Ulaanbaatar City Government",
        "project_number": "56001-002",
        "country": "Mongolia",
        "sector": "Energy",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(25),
        "deadline": _deadline(50),
        "budget_min": 20000000,
        "budget_max": 35000000,
    },
    {
        "external_id": "1123900",
        "url": "https://www.adb.org/node/1123900",
        "title": "Viet Nam: Ho Chi Minh City Urban Railway Line 2 - Signaling System",
        "description": "Procurement of signaling and train control systems (CBTC) for Metro Line 2.",
        "organization": "MAUR - Management Authority for Urban Railways",
        "project_number": "45200-005",
        "country": "Viet Nam",
        "sector": "Transport",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(28),
        "deadline": _deadline(55),
    },
    {
        "external_id": "1123750",
        "url": "https://www.adb.org/node/1123750",
        "title": "Philippines: Flood Risk Management in Metro Manila — Consulting Services",
        "description": "Consulting services for flood modeling, risk assessment, and design of resilient drainage infrastructure.",
        "organization": "DPWH - Department of Public Works and Highways",
        "project_number": "53347-001",
        "country": "Philippines",
        "sector": "Water and Urban Infrastructure",
        "procurement_type": "Individual Consulting",
        "published_at": _dt(30),
        "deadline": _deadline(10),
    },
    {
        "external_id": "1123600",
        "url": "https://www.adb.org/node/1123600",
        "title": "Kyrgyz Republic: Sustainable Energy Finance Facility — Solar PV",
        "description": "Supply and installation of 50MW solar photovoltaic power plant in Issyk-Kul province.",
        "organization": "National Energy Holding Company",
        "project_number": "55890-001",
        "country": "Kyrgyz Republic",
        "sector": "Energy",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(32),
        "deadline": _deadline(42),
        "budget_min": 30000000,
        "budget_max": 45000000,
    },
    {
        "external_id": "1123450",
        "url": "https://www.adb.org/node/1123450",
        "title": "Indonesia: Jakarta-Bandung High Speed Rail Extension Study",
        "description": "Feasibility study and preliminary engineering for the extension of the Jakarta-Bandung HSR to Surabaya.",
        "organization": "Ministry of Transportation, Indonesia",
        "project_number": "52199-002",
        "country": "Indonesia",
        "sector": "Transport",
        "procurement_type": "General Procurement Notice",
        "published_at": _dt(35),
        "deadline": _deadline(22),
    },
    {
        "external_id": "1123300",
        "url": "https://www.adb.org/node/1123300",
        "title": "Lao PDR: Secondary Education Quality Enhancement — IT Equipment",
        "description": "Supply of computers, networking equipment, and educational software for 200 secondary schools.",
        "organization": "Ministry of Education, Lao PDR",
        "project_number": "54789-001",
        "country": "Lao PDR",
        "sector": "Education",
        "procurement_type": "Invitation for Bids",
        "published_at": _dt(38),
        "deadline": _deadline(18),
    },
]

# ── WB Seed Data ─────────────────────────────────────────────

WB_SEEDS = [
    {
        "external_id": "WB-OP-2026-001",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-001",
        "title": "Ethiopia: Road Sector Development Program — Bridge Construction",
        "description": "Construction of 15 major bridges on the Addis Ababa-Mekelle corridor, including approach roads and drainage structures.",
        "organization": "Ethiopian Roads Authority",
        "project_number": "P178945",
        "country": "Ethiopia",
        "sector": "Transportation",
        "procurement_type": "Works",
        "published_at": _dt(5),
        "deadline": _deadline(30),
        "budget_min": 80000000,
        "budget_max": 120000000,
    },
    {
        "external_id": "WB-OP-2026-002",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-002",
        "title": "Nigeria: Digital Economy for Africa — Data Center Infrastructure",
        "description": "Design, supply, and installation of Tier-3 data center infrastructure in Lagos and Abuja.",
        "organization": "National Information Technology Development Agency",
        "project_number": "P176543",
        "country": "Nigeria",
        "sector": "Information and Communications Technologies",
        "procurement_type": "Goods",
        "published_at": _dt(8),
        "deadline": _deadline(40),
    },
    {
        "external_id": "WB-OP-2026-003",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-003",
        "title": "Morocco: Sustainable Water Management in Arid Regions",
        "description": "Consulting services for design of desalination plants and water distribution networks in Ouarzazate and Errachidia.",
        "organization": "ONEE - Office National de l'Electricité et de l'Eau Potable",
        "project_number": "P180012",
        "country": "Morocco",
        "sector": "Water Supply and Sanitation",
        "procurement_type": "Consultancy",
        "published_at": _dt(10),
        "deadline": _deadline(35),
    },
    {
        "external_id": "WB-OP-2026-004",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-004",
        "title": "Kenya: Affordable Housing Program — Construction Management",
        "description": "Project management consulting for construction of 10,000 affordable housing units in Nairobi and Mombasa.",
        "organization": "Kenya Mortgage Refinance Company",
        "project_number": "P175678",
        "country": "Kenya",
        "sector": "Social Protection",
        "procurement_type": "Consultancy",
        "published_at": _dt(12),
        "deadline": _deadline(28),
    },
    {
        "external_id": "WB-OP-2026-005",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-005",
        "title": "Bangladesh: Climate Resilient Agriculture and Food Security Project",
        "description": "Supply of irrigation equipment, climate-smart seeds, and post-harvest storage facilities for 50,000 smallholder farmers.",
        "organization": "Department of Agricultural Extension",
        "project_number": "P179876",
        "country": "Bangladesh",
        "sector": "Agriculture",
        "procurement_type": "Goods",
        "published_at": _dt(15),
        "deadline": _deadline(45),
    },
    {
        "external_id": "WB-OP-2026-006",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-006",
        "title": "Tanzania: Secondary Education Quality Improvement",
        "description": "Construction of 100 science laboratories and supply of laboratory equipment for secondary schools.",
        "organization": "Ministry of Education, Science and Technology",
        "project_number": "P177890",
        "country": "Tanzania",
        "sector": "Education",
        "procurement_type": "Works",
        "published_at": _dt(18),
        "deadline": _deadline(38),
    },
    {
        "external_id": "WB-OP-2026-007",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-007",
        "title": "Colombia: Urban Transport Modernization — Electric Bus Fleet",
        "description": "Procurement of 200 electric buses and charging infrastructure for Bogotá's TransMilenio system.",
        "organization": "TransMilenio S.A.",
        "project_number": "P178123",
        "country": "Colombia",
        "sector": "Transportation",
        "procurement_type": "Goods",
        "published_at": _dt(20),
        "deadline": _deadline(50),
        "budget_min": 150000000,
        "budget_max": 200000000,
    },
    {
        "external_id": "WB-OP-2026-008",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-008",
        "title": "Ghana: Renewable Energy Scaling Project — Solar Farm",
        "description": "EPC contract for 100MW solar photovoltaic farm in the Northern Region including grid connection.",
        "organization": "Ghana Grid Company",
        "project_number": "P179234",
        "country": "Ghana",
        "sector": "Energy",
        "procurement_type": "Works",
        "published_at": _dt(22),
        "deadline": _deadline(55),
        "budget_min": 60000000,
        "budget_max": 90000000,
    },
    {
        "external_id": "WB-OP-2026-009",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-009",
        "title": "Vietnam: Mekong Delta Climate Resilience — Coastal Protection",
        "description": "Design and construction of mangrove restoration and sea dike reinforcement along 50km of coastline.",
        "organization": "Ministry of Agriculture and Rural Development",
        "project_number": "P180456",
        "country": "Vietnam",
        "sector": "Environment",
        "procurement_type": "Works",
        "published_at": _dt(25),
        "deadline": _deadline(42),
    },
    {
        "external_id": "WB-OP-2026-010",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-010",
        "title": "Philippines: Digital Government Transformation — ERP System",
        "description": "Supply and implementation of enterprise resource planning system for 20 government agencies.",
        "organization": "Department of Information and Communications Technology",
        "project_number": "P176789",
        "country": "Philippines",
        "sector": "Information and Communications Technologies",
        "procurement_type": "Goods",
        "published_at": _dt(28),
        "deadline": _deadline(32),
    },
    {
        "external_id": "WB-OP-2026-011",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-011",
        "title": "India: National Health Mission — Telemedicine Platform",
        "description": "Development and deployment of AI-powered telemedicine platform serving 500 primary health centers.",
        "organization": "Ministry of Health and Family Welfare",
        "project_number": "P181234",
        "country": "India",
        "sector": "Health",
        "procurement_type": "Consultancy",
        "published_at": _dt(30),
        "deadline": _deadline(25),
    },
    {
        "external_id": "WB-OP-2026-012",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-012",
        "title": "Peru: Seismic Resilience in Schools — Retrofitting Program",
        "description": "Structural assessment and seismic retrofitting of 300 public school buildings in Lima and Arequipa.",
        "organization": "Ministry of Education, Peru",
        "project_number": "P177654",
        "country": "Peru",
        "sector": "Education",
        "procurement_type": "Works",
        "published_at": _dt(32),
        "deadline": _deadline(48),
    },
    {
        "external_id": "WB-OP-2026-013",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-013",
        "title": "Egypt: Cairo Metro Line 6 — Tunnel Boring & Station Construction",
        "description": "Civil works including tunnel boring, station construction, and ventilation systems for 20km metro extension.",
        "organization": "National Authority for Tunnels",
        "project_number": "P179567",
        "country": "Egypt",
        "sector": "Transportation",
        "procurement_type": "Works",
        "published_at": _dt(35),
        "deadline": _deadline(60),
        "budget_min": 1200000000,
        "budget_max": 1800000000,
    },
    {
        "external_id": "WB-OP-2026-014",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-014",
        "title": "Senegal: Rural Electrification — Mini-Grid Systems",
        "description": "Design, supply and installation of 50 solar mini-grid systems serving 200 villages in Casamance region.",
        "organization": "Agence Sénégalaise d'Électrification Rurale",
        "project_number": "P180789",
        "country": "Senegal",
        "sector": "Energy",
        "procurement_type": "Goods",
        "published_at": _dt(38),
        "deadline": _deadline(40),
    },
    {
        "external_id": "WB-OP-2026-015",
        "url": "https://projects.worldbank.org/procurement/WB-OP-2026-015",
        "title": "Jordan: Municipal Solid Waste Management — Landfill Remediation",
        "description": "Environmental remediation of Ghabawi landfill and construction of modern waste sorting and recycling facility.",
        "organization": "Greater Amman Municipality",
        "project_number": "P178901",
        "country": "Jordan",
        "sector": "Environment",
        "procurement_type": "Works",
        "published_at": _dt(40),
        "deadline": _deadline(35),
    },
]


async def seed(clear: bool = False) -> None:
    async with async_session() as db:
        if clear:
            await db.execute(delete(Opportunity).where(Opportunity.source.in_(["adb", "wb"])))
            await db.commit()
            logger.info("Cleared existing adb/wb opportunities")

        created = 0
        skipped = 0

        for source, seeds in [("adb", ADB_SEEDS), ("wb", WB_SEEDS)]:
            for data in seeds:
                # Check if exists
                result = await db.execute(
                    select(Opportunity).where(
                        Opportunity.source == source,
                        Opportunity.external_id == data["external_id"],
                    )
                )
                if result.scalar_one_or_none():
                    skipped += 1
                    continue

                opp = Opportunity(
                    id=uuid.uuid4(),
                    source=source,
                    external_id=data["external_id"],
                    url=data["url"],
                    title=data["title"],
                    description=data.get("description", ""),
                    organization=data.get("organization", ""),
                    project_number=data.get("project_number"),
                    published_at=data.get("published_at"),
                    deadline=data.get("deadline"),
                    budget_min=data.get("budget_min"),
                    budget_max=data.get("budget_max"),
                    currency=data.get("currency", "USD"),
                    location=data.get("location", ""),
                    country=data.get("country", ""),
                    sector=data.get("sector", ""),
                    procurement_type=data.get("procurement_type", ""),
                    status="open",
                )
                db.add(opp)
                created += 1

        await db.commit()
        logger.info("Seed complete: %d created, %d skipped (already exist)", created, skipped)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed opportunity data")
    parser.add_argument("--clear", action="store_true", help="Clear existing adb/wb data before seeding")
    args = parser.parse_args()
    asyncio.run(seed(clear=args.clear))
