"""add combined_ai_overview and combined_ai_reading_tips to projects

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-03-05 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a1b2"
down_revision: str | None = "b2c3d4e5f6a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("combined_ai_overview", sa.Text(), nullable=True))
    op.add_column("projects", sa.Column("combined_ai_reading_tips", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "combined_ai_reading_tips")
    op.drop_column("projects", "combined_ai_overview")
