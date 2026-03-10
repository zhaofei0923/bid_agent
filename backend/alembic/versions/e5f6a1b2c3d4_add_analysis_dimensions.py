"""add executive_summary, technical_requirements, technical_strategy, compliance_matrix to bid_analyses

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-03-10 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a1b2c3d4"
down_revision: str | None = "d4e5f6a1b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bid_analyses",
        sa.Column("executive_summary", JSONB(), nullable=True),
    )
    op.add_column(
        "bid_analyses",
        sa.Column("technical_requirements", JSONB(), nullable=True),
    )
    op.add_column(
        "bid_analyses",
        sa.Column("technical_strategy", JSONB(), nullable=True),
    )
    op.add_column(
        "bid_analyses",
        sa.Column("compliance_matrix", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bid_analyses", "compliance_matrix")
    op.drop_column("bid_analyses", "technical_strategy")
    op.drop_column("bid_analyses", "technical_requirements")
    op.drop_column("bid_analyses", "executive_summary")
