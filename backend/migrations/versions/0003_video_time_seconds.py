"""Add video_time_seconds to detection_history.

Revision ID: 0003_video_time_seconds
Revises: 0002_plate_kind_and_color
Create Date: 2026-07-20

Why this column exists
----------------------
Video processing already knew where in the clip each plate was found: the frame
loop tracks ``frame_index`` and ``_merge_frame_results`` carries it alongside the
best detection for each plate. It was then thrown away -- the docstring said so
in as many words, "kept for the log only".

The consequence is not obvious until someone uses the result. A thirty-second
clip yields a list of plates with no way to tell which vehicle passed when, and
no way to jump to the moment in the source video to check a doubtful reading.
For a system whose whole value is producing evidence, dropping the position of
the evidence within its own source is a real loss.

Seconds rather than frame index
-------------------------------
The stored value is a timestamp in seconds, not the raw frame number. A frame
index is only interpretable together with the clip's frame rate, which is not
stored anywhere and is not constant across sources -- a 25 fps CCTV export and a
60 fps phone recording would produce the same index for very different moments.
Converting once, at the point where the frame rate is known, keeps every
consumer from having to rediscover it.

Nullable, with no default
-------------------------
``NULL`` means "this detection did not come from a video", which is the truth for
every image and realtime-frame result and for every row written before this
migration. A default of ``0.0`` would be indistinguishable from a plate found in
the opening frame.
"""

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
