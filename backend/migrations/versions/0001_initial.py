"""Initial schema: detection_job and detection_history.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UUID_LENGTH = 36
_PATH_LENGTH = 512
_PLATE_LENGTH = 32
_ENUM_LENGTH = 16


def upgrade() -> None:
    """Create the detection_job and detection_history tables."""
    op.create_table(
        "detection_job",
        sa.Column("id", sa.String(length=_UUID_LENGTH), nullable=False),
        sa.Column("input_type", sa.String(length=_ENUM_LENGTH), nullable=False),
        sa.Column("status", sa.String(length=_ENUM_LENGTH), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("source_path", sa.String(length=_PATH_LENGTH), nullable=True),
        sa.Column("output_path", sa.String(length=_PATH_LENGTH), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("total_frames", sa.Integer(), nullable=True),
        sa.Column("processed_frames", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_detection_job"),
        sa.CheckConstraint(
            "input_type IN ('image', 'video', 'webcam')",
            name="ck_detection_job_input_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name="ck_detection_job_status",
        ),
        sa.CheckConstraint(
            "progress >= 0.0 AND progress <= 1.0",
            name="ck_detection_job_progress_range",
        ),
    )
    op.create_index("ix_detection_job_input_type", "detection_job", ["input_type"])
    op.create_index("ix_detection_job_status", "detection_job", ["status"])
    op.create_index("ix_detection_job_created_at", "detection_job", ["created_at"])

    op.create_table(
        "detection_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plate_number", sa.String(length=_PLATE_LENGTH), nullable=True),
        sa.Column("raw_ocr_text", sa.String(length=_PLATE_LENGTH), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("input_type", sa.String(length=_ENUM_LENGTH), nullable=False),
        sa.Column("image_path", sa.String(length=_PATH_LENGTH), nullable=True),
        sa.Column("plate_image_path", sa.String(length=_PATH_LENGTH), nullable=True),
        sa.Column("bbox_x", sa.Integer(), nullable=False),
        sa.Column("bbox_y", sa.Integer(), nullable=False),
        sa.Column("bbox_w", sa.Integer(), nullable=False),
        sa.Column("bbox_h", sa.Integer(), nullable=False),
        sa.Column("is_valid_format", sa.Boolean(), nullable=False),
        sa.Column("plate_line_count", sa.Integer(), nullable=True),
        sa.Column("processing_time", sa.Float(), nullable=False),
        sa.Column("detected_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_job_id", sa.String(length=_UUID_LENGTH), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_detection_history"),
        sa.ForeignKeyConstraint(
            ["source_job_id"],
            ["detection_job.id"],
            name="fk_detection_history_source_job_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "input_type IN ('image', 'video', 'webcam')",
            name="ck_detection_history_input_type",
        ),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_detection_history_confidence_range",
        ),
        sa.CheckConstraint(
            "ocr_confidence IS NULL OR (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0)",
            name="ck_detection_history_ocr_confidence_range",
        ),
        sa.CheckConstraint(
            "plate_line_count IS NULL OR plate_line_count IN (1, 2)",
            name="ck_detection_history_plate_line_count",
        ),
        sa.CheckConstraint(
            "bbox_w > 0 AND bbox_h > 0",
            name="ck_detection_history_bbox_positive",
        ),
    )
    op.create_index("ix_detection_history_plate_number", "detection_history", ["plate_number"])
    op.create_index("ix_detection_history_detected_time", "detection_history", ["detected_time"])
    op.create_index("ix_detection_history_input_type", "detection_history", ["input_type"])
    op.create_index("ix_detection_history_source_job_id", "detection_history", ["source_job_id"])
    op.create_index(
        "ix_detection_history_input_type_detected_time",
        "detection_history",
        ["input_type", "detected_time"],
    )


def downgrade() -> None:
    """Drop both tables, children before parents."""
    op.drop_index(
        "ix_detection_history_input_type_detected_time",
        table_name="detection_history",
    )
    op.drop_index("ix_detection_history_source_job_id", table_name="detection_history")
    op.drop_index("ix_detection_history_input_type", table_name="detection_history")
    op.drop_index("ix_detection_history_detected_time", table_name="detection_history")
    op.drop_index("ix_detection_history_plate_number", table_name="detection_history")
    op.drop_table("detection_history")

    op.drop_index("ix_detection_job_created_at", table_name="detection_job")
    op.drop_index("ix_detection_job_status", table_name="detection_job")
    op.drop_index("ix_detection_job_input_type", table_name="detection_job")
    op.drop_table("detection_job")
