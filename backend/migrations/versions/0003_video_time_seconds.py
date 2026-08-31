"""Add video_time_seconds to detection_history."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic.
revision: str = "0003_video_time_seconds"
down_revision: str | None = "0002_plate_kind_and_color"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the video timestamp column."""
    op.add_column(
        "detection_history",
        sa.Column("video_time_seconds", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Drop the column, rebuilding the table as SQLite requires."""
    with op.batch_alter_table("detection_history") as batch:
        batch.drop_column("video_time_seconds")
