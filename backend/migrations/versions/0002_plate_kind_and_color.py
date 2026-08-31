"""Add plate_kind, plate_color and plate_color_confidence to detection_history.

Revision ID: 0002_plate_kind_and_color
Revises: 0001_initial
Create Date: 2026-07-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic.
revision: str = "0002_plate_kind_and_color"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ENUM_LENGTH = 16


def upgrade() -> None:
    """Add the three vehicle-class columns."""
    op.add_column(
        "detection_history",
        sa.Column("plate_kind", sa.String(length=_ENUM_LENGTH), nullable=True),
    )
    op.add_column(
        "detection_history",
        sa.Column("plate_color", sa.String(length=_ENUM_LENGTH), nullable=True),
    )
    op.add_column(
        "detection_history",
        sa.Column("plate_color_confidence", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Drop the three columns, rebuilding the table as SQLite requires."""
    with op.batch_alter_table("detection_history") as batch:
        batch.drop_column("plate_color_confidence")
        batch.drop_column("plate_color")
        batch.drop_column("plate_kind")
