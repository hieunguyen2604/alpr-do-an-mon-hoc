"""Add upper_char_count to detection_history.

Revision ID: 0004_upper_char_count
Revises: 0003_video_time_seconds
Create Date: 2026-08-02

Why this column exists
----------------------
An eight-character two-line plate string is genuinely ambiguous, and no rule
over the string can resolve it::

    67C10815  ->  67C-108.15   when the upper line reads  67C   (serial C,  5 digits)
    67C10815  ->  67C1-0815    when the upper line reads  67C1  (serial C1, 4 digits)

Both readings are legal Vietnamese plates. The only evidence that separates
them is *where the plate's own line break falls* -- and the split-then-hstack
step that makes a two-line plate readable at all is precisely what discards it.

The recogniser can recover the observation for free: after the halves are
stacked side by side, OCR returns one text fragment per half, so the length of
the first fragment is the upper line's character count. Measured on the demo
set, deriving the grouping from the plate family instead got five of seven such
plates right and two wrong (``77H54374`` rendered ``77H-543.74`` instead of
``77H5-4374``); the upper-line count gets all seven right.

Evidence, not presentation
--------------------------
Separators are still **derived on read** in
``backend/services/detection_service.display_text`` -- this migration does not
change that, and does not store a formatted string. What it stores is the
observation the derivation needs, in the same spirit as ``plate_line_count``
and ``plate_kind``: the row records what was seen, the read path decides how to
show it.

Nullable on purpose
-------------------
Rows written before this migration have no value, and a back-filled guess would
be indistinguishable from a measurement. ``NULL`` reads as "not recorded".
One-line plates are also ``NULL``: there is no upper line to count.

Why the CHECK is (3, 4)
-----------------------
The upper line of a Vietnamese two-line plate carries the province code plus
the serial: three characters (``67C``) or four (``77H5``). Nothing else is a
legal reading, so any other value means the count was miscomputed rather than
observed, and the constraint stops it before it can reach the display rule.

No batch mode needed for the column
-----------------------------------
SQLite performs a plain ``ADD COLUMN`` for a nullable column without rebuilding
the table, so no existing constraint can be silently lost. The CHECK constraint
and the downgrade both need batch mode, because SQLite implements them by
recreating the table.
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
