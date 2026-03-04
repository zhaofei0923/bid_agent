"""add bds_modifications and risk_assessment to bid_analyses

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-03 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a1"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bid_analyses",
        sa.Column("bds_modifications", JSONB(), nullable=True),
    )
    op.add_column(
        "bid_analyses",
        sa.Column("risk_assessment", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bid_analyses", "risk_assessment")
    op.drop_column("bid_analyses", "bds_modifications")
