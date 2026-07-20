"""Unit tests for :mod:`backend.schemas.detection`.

The schemas are the API's wire contract, so these tests are contract tests. Two
themes run through them:

**Bounds are enforced, not documented.** A confidence outside ``[0, 1]`` or a
line count of 3 must be rejected at the boundary rather than stored and later
charted. Pydantic does the work; the tests state which bounds were intended, so
that relaxing one is a deliberate act with a failing test attached.

**The two confidences and the two counting families stay separate.** A low
detection confidence and a low OCR confidence mean entirely different things,
and one image containing three plates is one job and three detections. Both
distinctions are structural in the schema, and both are checked here.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from backend.schemas.detection import (
    BoundingBoxSchema,
    DailyCountSchema,
    DetectionHistoryResponse,
    DetectionJobResponse,
    DetectionResponse,
    DetectionResultSchema,
    ErrorResponse,
    HealthResponse,
    HistoryListResponse,
    InputTypeCountSchema,
    StatisticsResponse,
)

_NOW = dt.datetime(2026, 7, 19, 9, 31, 22, tzinfo=dt.timezone.utc)


def history_payload(**overrides: Any) -> dict[str, Any]:
    """Build a complete, valid history-record payload.

    Args:
        **overrides: Fields to replace in the baseline.

    Returns:
        A dictionary accepted by :class:`DetectionHistoryResponse`.
    """
    payload: dict[str, Any] = {
        "id": 1247,
        "plate_number": "51F-12345",
        "raw_ocr_text": "51FI2345",
        "confidence": 0.94,
        "ocr_confidence": 0.87,
        "input_type": "image",
        "image_path": "/files/uploads/a.jpg",
        "plate_image_path": "/files/plates/a-plate-0.jpg",
        "bbox_x": 142,
        "bbox_y": 318,
        "bbox_w": 186,
        "bbox_h": 64,
        "is_valid_format": True,
        "plate_line_count": 1,
        "processing_time": 0.412,
        "detected_time": _NOW,
        "created_at": _NOW,
        "source_job_id": "3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840",
    }
    payload.update(overrides)
    return payload


class TestBoundingBoxSchema:
    """The one coordinate convention used end to end."""

    def test_accepts_a_well_formed_box(self) -> None:
        box = BoundingBoxSchema(x=142, y=318, width=186, height=64)
        assert (box.x, box.y, box.width, box.height) == (142, 318, 186, 64)

    def test_an_origin_at_zero_is_valid(self) -> None:
        assert BoundingBoxSchema(x=0, y=0, width=1, height=1).x == 0

    @pytest.mark.parametrize(("field", "value"), [("x", -1), ("y", -5)])
    def test_rejects_a_negative_origin(self, field: str, value: int) -> None:
        payload = {"x": 0, "y": 0, "width": 10, "height": 10, field: value}
        with pytest.raises(PydanticValidationError):
            BoundingBoxSchema(**payload)

    @pytest.mark.parametrize(("field", "value"), [("width", 0), ("height", 0), ("width", -3)])
    def test_rejects_a_degenerate_box(self, field: str, value: int) -> None:
        """A zero-area box cannot be cropped and must not reach the client."""
        payload = {"x": 0, "y": 0, "width": 10, "height": 10, field: value}
        with pytest.raises(PydanticValidationError):
            BoundingBoxSchema(**payload)


class TestDetectionResultSchema:
    """One plate found during a run."""

    def test_accepts_a_complete_result(self) -> None:
        result = DetectionResultSchema(
            plate_number="51F-12345",
            raw_ocr_text="51FI2345",
            detection_confidence=0.94,
            ocr_confidence=0.87,
            bbox=BoundingBoxSchema(x=1, y=2, width=3, height=4),
            is_valid_format=True,
            plate_line_count=1,
            processing_time=0.4,
        )
        assert result.plate_number == "51F-12345"

    def test_an_unread_plate_is_representable(self) -> None:
        """A detection with no text is a real, reportable outcome.

        Making these fields mandatory would force the persistence layer to
        invent a value, which is how recognition failures disappear from the
        accuracy figures.
        """
        result = DetectionResultSchema(
            detection_confidence=0.7,
            bbox=BoundingBoxSchema(x=1, y=2, width=3, height=4),
        )
        assert result.plate_number is None
        assert result.raw_ocr_text is None
        assert result.ocr_confidence is None
        assert result.is_valid_format is False

    def test_the_two_confidences_are_independent_fields(self) -> None:
        """A high detection confidence with a low OCR one must be expressible.

        That combination is the common case for a blurred plate, and merging
        the two numbers would make it indistinguishable from an uncertain
        detection.
        """
        result = DetectionResultSchema(
            detection_confidence=0.99,
            ocr_confidence=0.10,
            bbox=BoundingBoxSchema(x=1, y=2, width=3, height=4),
        )
        assert result.detection_confidence == 0.99
        assert result.ocr_confidence == 0.10

    @pytest.mark.parametrize("value", [-0.01, 1.01, 2.0, -1.0])
    def test_rejects_a_detection_confidence_outside_zero_to_one(self, value: float) -> None:
        with pytest.raises(PydanticValidationError):
            DetectionResultSchema(
                detection_confidence=value,
                bbox=BoundingBoxSchema(x=1, y=2, width=3, height=4),
            )

    @pytest.mark.parametrize("value", [-0.01, 1.01])
    def test_rejects_an_ocr_confidence_outside_zero_to_one(self, value: float) -> None:
        with pytest.raises(PydanticValidationError):
            DetectionResultSchema(
                detection_confidence=0.5,
                ocr_confidence=value,
                bbox=BoundingBoxSchema(x=1, y=2, width=3, height=4),
            )

    @pytest.mark.parametrize("value", [0, 3, -1, 10])
    def test_rejects_a_line_count_other_than_one_or_two(self, value: int) -> None:
        """Vietnamese plates carry one line or two; there is no third case."""
        with pytest.raises(PydanticValidationError):
            DetectionResultSchema(
                detection_confidence=0.5,
                plate_line_count=value,
                bbox=BoundingBoxSchema(x=1, y=2, width=3, height=4),
            )

    def test_rejects_a_negative_processing_time(self) -> None:
        with pytest.raises(PydanticValidationError):
            DetectionResultSchema(
                detection_confidence=0.5,
                processing_time=-0.1,
                bbox=BoundingBoxSchema(x=1, y=2, width=3, height=4),
            )


class TestDetectionResponse:
    """The wrapper returned by the image and frame endpoints."""

    def test_an_image_with_no_plate_is_a_valid_successful_response(self) -> None:
        """Not a 4xx: treating "found nothing" as an error would erase every
        negative case from the statistics."""
        response = DetectionResponse(
            job_id="job-1",
            input_type="image",
            results=[],
            plate_count=0,
            processing_time=0.3,
        )
        assert response.results == []
        assert response.plate_count == 0

    def test_carries_several_plates_under_one_job_id(self) -> None:
        """Three plates, one upload -- the grouping the whole API depends on."""
        results = [
            DetectionResultSchema(
                detection_confidence=0.9,
                bbox=BoundingBoxSchema(x=index, y=1, width=10, height=5),
            )
            for index in range(3)
        ]
        response = DetectionResponse(
            job_id="job-1",
            input_type="image",
            results=results,
            plate_count=len(results),
            processing_time=0.8,
        )
        assert response.plate_count == 3
        assert response.job_id == "job-1"

    @pytest.mark.parametrize("value", ["satellite", "IMAGE", "", "photo"])
    def test_rejects_an_input_type_outside_the_three(self, value: str) -> None:
        with pytest.raises(PydanticValidationError):
            DetectionResponse(
                job_id="job-1",
                input_type=value,
                plate_count=0,
                processing_time=0.1,
            )

    def test_rejects_a_negative_plate_count(self) -> None:
        with pytest.raises(PydanticValidationError):
            DetectionResponse(
                job_id="job-1",
                input_type="image",
                plate_count=-1,
                processing_time=0.1,
            )

    def test_a_webcam_frame_has_no_image_url(self) -> None:
        """Frames are not persisted, so there is nothing to link to."""
        response = DetectionResponse(
            job_id="job-1",
            input_type="webcam",
            plate_count=0,
            processing_time=0.1,
            image_url=None,
        )
        assert response.image_url is None


class TestDetectionHistoryResponse:
    """One stored record, including its computed nested box."""

    def test_accepts_a_complete_record(self) -> None:
        record = DetectionHistoryResponse(**history_payload())
        assert record.id == 1247
        assert record.source_job_id.startswith("3f2a")

    def test_exposes_the_box_in_both_flat_and_nested_form(self) -> None:
        """The columns are flat in the database; a client drawing an overlay
        wants one object, so the response carries both."""
        record = DetectionHistoryResponse(**history_payload())
        assert record.bbox.x == record.bbox_x
        assert record.bbox.y == record.bbox_y
        assert record.bbox.width == record.bbox_w
        assert record.bbox.height == record.bbox_h

    def test_the_nested_box_is_serialised(self) -> None:
        dumped = DetectionHistoryResponse(**history_payload()).model_dump()
        assert dumped["bbox"] == {"x": 142, "y": 318, "width": 186, "height": 64}

    def test_an_unread_record_is_representable(self) -> None:
        record = DetectionHistoryResponse(
            **history_payload(
                plate_number=None,
                raw_ocr_text=None,
                ocr_confidence=None,
                is_valid_format=False,
                plate_line_count=None,
            )
        )
        assert record.plate_number is None
        assert record.ocr_confidence is None

    def test_maps_from_an_object_by_attribute(self) -> None:
        """``from_attributes`` is what lets a router return an ORM row."""

        class Row:
            pass

        row = Row()
        for key, value in history_payload().items():
            setattr(row, key, value)

        record = DetectionHistoryResponse.model_validate(row)
        assert record.plate_number == "51F-12345"
        assert record.bbox.width == 186

    def test_the_raw_and_corrected_strings_are_both_carried(self) -> None:
        """Comparing them is the only way to measure post-processing."""
        record = DetectionHistoryResponse(**history_payload())
        assert record.plate_number != record.raw_ocr_text
        assert record.raw_ocr_text == "51FI2345"


class TestHistoryListResponse:
    """Pagination arithmetic, computed in one place."""

    @pytest.mark.parametrize(
        ("total", "page_size", "expected"),
        [
            (0, 20, 0),
            (1, 20, 1),
            (20, 20, 1),
            (21, 20, 2),
            (1247, 20, 63),
            (100, 10, 10),
            (101, 10, 11),
        ],
    )
    def test_total_pages_rounds_up(self, total: int, page_size: int, expected: int) -> None:
        """``total // page_size`` would silently drop the final partial page."""
        response = HistoryListResponse.build(items=[], total=total, page=1, page_size=page_size)
        assert response.total_pages == expected

    def test_navigation_flags_on_the_first_page(self) -> None:
        response = HistoryListResponse.build(items=[], total=100, page=1, page_size=20)
        assert response.has_previous is False
        assert response.has_next is True

    def test_navigation_flags_on_the_last_page(self) -> None:
        response = HistoryListResponse.build(items=[], total=100, page=5, page_size=20)
        assert response.has_previous is True
        assert response.has_next is False

    def test_navigation_flags_on_a_single_page(self) -> None:
        response = HistoryListResponse.build(items=[], total=5, page=1, page_size=20)
        assert response.has_next is False
        assert response.has_previous is False

    def test_an_empty_result_set_is_valid(self) -> None:
        response = HistoryListResponse.build(items=[], total=0, page=1, page_size=20)
        assert response.items == []
        assert response.total_pages == 0
        assert response.has_next is False

    def test_builds_items_from_payloads(self) -> None:
        response = HistoryListResponse.build(
            items=[history_payload(id=1), history_payload(id=2)],
            total=2,
            page=1,
            page_size=20,
        )
        assert [item.id for item in response.items] == [1, 2]

    def test_the_navigation_flags_are_serialised(self) -> None:
        dumped = HistoryListResponse.build(items=[], total=100, page=2, page_size=20).model_dump()
        assert dumped["has_next"] is True
        assert dumped["has_previous"] is True

    def test_rejects_a_page_below_one(self) -> None:
        with pytest.raises(PydanticValidationError):
            HistoryListResponse(items=[], total=0, page=0, page_size=20, total_pages=0)

    def test_rejects_a_negative_total(self) -> None:
        with pytest.raises(PydanticValidationError):
            HistoryListResponse(items=[], total=-1, page=1, page_size=20, total_pages=0)


class TestDetectionJobResponse:
    """Job state, minus the technical failure text."""

    def test_accepts_a_running_job(self) -> None:
        job = DetectionJobResponse(
            id="job-1",
            input_type="video",
            status="processing",
            progress=0.65,
            total_frames=1800,
            processed_frames=234,
            detection_count=7,
            created_at=_NOW,
        )
        assert job.progress == 0.65
        assert job.completed_at is None

    @pytest.mark.parametrize(
        "status", ["pending", "processing", "completed", "failed", "cancelled"]
    )
    def test_accepts_every_declared_status(self, status: str) -> None:
        job = DetectionJobResponse(
            id="job-1",
            input_type="video",
            status=status,
            progress=0.0,
            created_at=_NOW,
        )
        assert job.status == status

    @pytest.mark.parametrize("status", ["queued", "done", "PENDING", ""])
    def test_rejects_an_undeclared_status(self, status: str) -> None:
        with pytest.raises(PydanticValidationError):
            DetectionJobResponse(
                id="job-1",
                input_type="video",
                status=status,
                progress=0.0,
                created_at=_NOW,
            )

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_a_progress_outside_zero_to_one(self, value: float) -> None:
        with pytest.raises(PydanticValidationError):
            DetectionJobResponse(
                id="job-1",
                input_type="video",
                status="processing",
                progress=value,
                created_at=_NOW,
            )

    def test_the_error_message_is_not_part_of_the_contract(self) -> None:
        """NFR-S4: the technical reason belongs in the log, never in a response.

        Asserting on the field list rather than on one payload, so that adding
        the field back to the schema fails here regardless of how it is
        populated.
        """
        assert "error_message" not in DetectionJobResponse.model_fields

    def test_an_unknown_field_is_ignored_rather_than_serialised(self) -> None:
        job = DetectionJobResponse.model_validate(
            {
                "id": "job-1",
                "input_type": "video",
                "status": "failed",
                "progress": 1.0,
                "created_at": _NOW,
                "error_message": "OSError: disk full at /srv/data",
            }
        )
        assert "error_message" not in job.model_dump()
        assert "disk full" not in str(job.model_dump())


class TestStatisticsResponse:
    """Jobs versus detections, kept apart by name."""

    def test_accepts_a_full_set_of_figures(self) -> None:
        stats = StatisticsResponse(
            total_jobs=412,
            total_detections=689,
            unique_plates=574,
            valid_format_count=601,
            invalid_format_count=52,
            unreadable_count=36,
            average_confidence=0.912,
            average_ocr_confidence=0.864,
            average_processing_time=0.437,
            jobs_today=12,
            detections_today=19,
        )
        assert stats.total_jobs == 412
        assert stats.total_detections == 689

    def test_the_two_counting_families_are_separate_fields(self) -> None:
        """One image with three plates is one job and three detections.

        A single ``total`` field would make the distinction unrepresentable and
        the dashboard wrong by the average plates-per-image factor.
        """
        assert "total_jobs" in StatisticsResponse.model_fields
        assert "total_detections" in StatisticsResponse.model_fields

    def test_averages_may_be_null_on_an_empty_database(self) -> None:
        """``0.0`` would read as "the model is certain of nothing"."""
        stats = StatisticsResponse(
            total_jobs=0,
            total_detections=0,
            unique_plates=0,
            valid_format_count=0,
            invalid_format_count=0,
        )
        assert stats.average_confidence is None
        assert stats.average_ocr_confidence is None
        assert stats.average_processing_time is None

    @pytest.mark.parametrize(
        "field",
        [
            "total_jobs",
            "total_detections",
            "unique_plates",
            "valid_format_count",
            "invalid_format_count",
            "unreadable_count",
            "jobs_today",
            "detections_today",
        ],
    )
    def test_no_counter_may_be_negative(self, field: str) -> None:
        payload: dict[str, Any] = {
            "total_jobs": 0,
            "total_detections": 0,
            "unique_plates": 0,
            "valid_format_count": 0,
            "invalid_format_count": 0,
            field: -1,
        }
        with pytest.raises(PydanticValidationError):
            StatisticsResponse(**payload)

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_an_average_confidence_stays_within_zero_to_one(self, value: float) -> None:
        with pytest.raises(PydanticValidationError):
            StatisticsResponse(
                total_jobs=1,
                total_detections=1,
                unique_plates=1,
                valid_format_count=1,
                invalid_format_count=0,
                average_confidence=value,
            )

    def test_carries_the_breakdowns(self) -> None:
        stats = StatisticsResponse(
            total_jobs=1,
            total_detections=3,
            unique_plates=3,
            valid_format_count=3,
            invalid_format_count=0,
            by_input_type=[
                InputTypeCountSchema(input_type="image", job_count=1, detection_count=3)
            ],
            daily_counts=[DailyCountSchema(date=_NOW.date(), job_count=1, detection_count=3)],
        )
        assert stats.by_input_type[0].job_count == 1
        assert stats.by_input_type[0].detection_count == 3
        assert stats.daily_counts[0].date == _NOW.date()

    def test_a_breakdown_entry_rejects_an_unknown_input_type(self) -> None:
        with pytest.raises(PydanticValidationError):
            InputTypeCountSchema(input_type="satellite", job_count=1, detection_count=1)


class TestHealthResponse:
    """Readiness, not mere liveness."""

    @pytest.mark.parametrize("status", ["ok", "degraded"])
    def test_accepts_the_two_declared_states(self, status: str) -> None:
        health = HealthResponse(
            status=status,
            app_name="Vietnamese ALPR API",
            version="0.1.0",
            database_connected=True,
            model_loaded=True,
            uptime_seconds=12.5,
            timestamp=_NOW,
        )
        assert health.status == status

    def test_rejects_an_undeclared_state(self) -> None:
        with pytest.raises(PydanticValidationError):
            HealthResponse(
                status="fine",
                app_name="x",
                version="1",
                database_connected=True,
                model_loaded=True,
                uptime_seconds=1.0,
                timestamp=_NOW,
            )

    def test_the_model_loaded_field_survives_the_protected_namespace(self) -> None:
        """``model_`` is reserved by Pydantic; the guard is disabled, not the name."""
        assert "model_loaded" in HealthResponse.model_fields

    def test_rejects_a_negative_uptime(self) -> None:
        with pytest.raises(PydanticValidationError):
            HealthResponse(
                status="ok",
                app_name="x",
                version="1",
                database_connected=True,
                model_loaded=True,
                uptime_seconds=-1.0,
                timestamp=_NOW,
            )


class TestErrorResponse:
    """The single body shape every failure uses."""

    def test_carries_a_code_a_message_and_a_request_id(self) -> None:
        error = ErrorResponse(
            error="FILE_TOO_LARGE",
            message="Tệp tải lên quá lớn.",
            request_id="8c1d4f9a",
        )
        assert error.error == "FILE_TOO_LARGE"
        assert error.request_id == "8c1d4f9a"

    def test_the_request_id_is_optional(self) -> None:
        """A failure before the middleware ran has no identifier to report."""
        assert ErrorResponse(error="X", message="y").request_id is None

    def test_the_schema_has_no_field_for_a_traceback(self) -> None:
        """NFR-S4, expressed as an absence rather than as a redaction step.

        A field that does not exist cannot be populated by accident, which is
        stronger than remembering to strip one.
        """
        forbidden = {"traceback", "stack_trace", "detail", "exception", "stacktrace"}
        assert forbidden.isdisjoint(set(ErrorResponse.model_fields))
