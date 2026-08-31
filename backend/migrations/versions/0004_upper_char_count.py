"""Add upper_char_count to detection_history.

Revision ID: 0004_upper_char_count
Revises: 0003_video_time_seconds
Create Date: 2026-08-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic.
revision: str = "0004_upper_char_count"
down_revision: str | None = "0003_video_time_seconds"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHECK_NAME = "ck_detection_history_upper_char_count"


def upgrade() -> None:
    """Add the column, then its range constraint."""
    op.add_column(
        "detection_history",
        sa.Column("upper_char_count", sa.Integer(), nullable=True),
    )
    with op.batch_alter_table("detection_history") as batch:
        batch.create_check_constraint(
            _CHECK_NAME,
            "upper_char_count IS NULL OR upper_char_count IN (3, 4)",
        )


def downgrade() -> None:
    """Drop the constraint and the column, rebuilding the table."""
    with op.batch_alter_table("detection_history") as batch:
        batch.drop_constraint(_CHECK_NAME, type_="check")
        batch.drop_column("upper_char_count")
