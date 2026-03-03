"""add is_verified to users

Revision ID: a1b2c3d4e5f6
Revises: 696cef558d26
Create Date: 2026-03-03 10:00:00.000000
"""

from typing import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "696cef558d26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add column as nullable first so existing rows are handled
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=True))
    # Mark all existing users as already verified to avoid lockout
    op.execute("UPDATE users SET is_verified = TRUE")
    # Make the column non-nullable with server default false for new registrations
    op.alter_column(
        "users",
        "is_verified",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )


def downgrade() -> None:
    op.drop_column("users", "is_verified")
