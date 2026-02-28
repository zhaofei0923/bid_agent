"""add_search_vector_trigger

Revision ID: 696cef558d26
Revises: 78e8d802ab2c
Create Date: 2026-02-21 11:59:04.653920
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '696cef558d26'
down_revision: Union[str, None] = '78e8d802ab2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create trigger function for auto-updating search_vector
    op.execute("""
        CREATE OR REPLACE FUNCTION opportunities_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.organization, '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(NEW.country, '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(NEW.sector, '')), 'C');
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger on opportunities table
    op.execute("""
        CREATE TRIGGER trig_opportunities_search_vector
          BEFORE INSERT OR UPDATE ON opportunities
          FOR EACH ROW EXECUTE FUNCTION opportunities_search_vector_update();
    """)

    # Backfill existing rows
    op.execute("""
        UPDATE opportunities SET search_vector =
          setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
          setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
          setweight(to_tsvector('english', COALESCE(organization, '')), 'C') ||
          setweight(to_tsvector('english', COALESCE(country, '')), 'C') ||
          setweight(to_tsvector('english', COALESCE(sector, '')), 'C');
    """)

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_opportunities_search_vector
          ON opportunities USING GIN (search_vector);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_opportunities_search_vector;")
    op.execute("DROP TRIGGER IF EXISTS trig_opportunities_search_vector ON opportunities;")
    op.execute("DROP FUNCTION IF EXISTS opportunities_search_vector_update();")

