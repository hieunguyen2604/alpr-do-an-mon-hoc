"""Add plate_kind, plate_color and plate_color_confidence to detection_history.

Revision ID: 0002_plate_kind_and_color
Revises: 0001_initial
Create Date: 2026-07-20

Why these columns exist
-----------------------
The recognition stage already classified every plate into a family (car,
motorcycle, state agency, diplomatic, army...) and then threw the answer away
before anything was written to this table. The visible consequence: an army
plate -- correctly read as ``KV6938`` at 0.999 OCR confidence -- was stored with
``is_valid_format = 0`` and nothing else, indistinguishable from a plate the
system had failed to read. The interface then showed it to the user as "wrong
plate format", which is untrue: an army plate is a perfectly valid plate that
simply sits outside the civil registration system.

``plate_color`` records something no rule over the character string can recover.
Circular 79/2024/TT-BCA gives a commercial vehicle a **yellow** plate carrying
exactly the same layout as a private vehicle's **white** one, so the two are
identical as strings and separable only by colour.

Neither column identifies a vehicle class on its own, and that is why both are
stored: colour cannot tell a diplomatic plate from a private one (both white),
and the string cannot tell a business car from a private one (both ``CAR``).

Nullable on purpose
-------------------
Every column here is nullable with no default. Rows written before this
migration genuinely have no value -- the information was never computed for
them -- and back-filling a guess would be indistinguishable from a measurement.
``NULL`` reads as "not recorded", which is the truth.

No batch mode needed
--------------------
SQLite supports plain ``ADD COLUMN`` for nullable columns without a table
rebuild, so no constraint can be silently lost here. The downgrade does need
batch mode, because dropping a column is one of the operations SQLite performs
by recreating the table.
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
"""Matches ``_ENUM_LENGTH`` in ``backend/models/detection.py``.

The longest value stored is ``motorcycle_new`` at 14 characters, so the two
spare characters are the whole margin. A future plate family with a longer name
needs its own migration -- which is the intended trade-off: the constant is
shared with the enum columns that already exist, and widening it here alone
would make the model and the schema disagree.
"""


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
