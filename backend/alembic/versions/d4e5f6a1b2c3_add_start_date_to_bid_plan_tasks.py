"""add start_date to bid_plan_tasks

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-03-09 14:30:00.000000

"""
from typing import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a1b2c3"
down_revision: str | None = "c3d4e5f6a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bid_plan_tasks", sa.Column("start_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("bid_plan_tasks", "start_date")
