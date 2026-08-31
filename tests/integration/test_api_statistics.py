"""Integration tests for the dashboard statistics endpoint."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.detection import DetectionHistory, DetectionJob, InputType

from .conftest import FakePipeline, encode_jpeg

pytestmark = pytest.mark.integration

STATISTICS_URL = "/api/statistics"
IMAGE_URL = "/api/detect/image"


def upload_image(client: TestClient) -> dict:
    """Upload one image through the real endpoint."""
    response = client.post(IMAGE_URL, files={"file": ("car.jpg", encode_jpeg(), "image/jpeg")})
    assert response.status_code == 200
    return response.json()


class TestCountingJobsVersusPlates:
    """One upload with three plates is ONE use of the system."""

    def test_one_image_with_three_plates_is_one_job_and_three_detections(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """The single most important assertion in the statistics layer."""
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
            ("30G-33333", "30G33333", 0.7, 0.6, True),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["total_jobs"] == 1
        assert stats["total_detections"] == 3

    def test_three_separate_images_are_three_jobs(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [("51F-11111", "51F11111", 0.9, 0.8, True)]
        for _ in range(3):
            upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["total_jobs"] == 3
        assert stats["total_detections"] == 3

    def test_the_two_figures_diverge_as_soon_as_they_can(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """Two uploads, five plates: the figures must not be equal."""
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
            ("30G-33333", "30G33333", 0.7, 0.6, True),
        ]
        upload_image(client)

        pipeline.plates = [
            ("51F-44444", "51F44444", 0.9, 0.8, True),
            ("29A1-55555", "29A155555", 0.8, 0.7, True),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["total_jobs"] == 2
        assert stats["total_detections"] == 5

    def test_an_upload_that_found_nothing_still_counts_as_usage(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """The user did upload the image, so the usage figure must include it."""
        pipeline.plates = []
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["total_jobs"] == 1
        assert stats["total_detections"] == 0

    def test_a_twenty_plate_image_is_still_one_job(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [
            (f"51F-{index:05d}", f"51F{index:05d}", 0.9, 0.8, True) for index in range(20)
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["total_jobs"] == 1
        assert stats["total_detections"] == 20

    def test_today_counters_follow_the_same_rule(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["jobs_today"] == 1
        assert stats["detections_today"] == 2

    def test_a_webcam_session_of_many_frames_is_one_job(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """Otherwise a thirty-second capture reads as hundreds of uploads."""
        pipeline.plates = [("51F-11111", "51F11111", 0.9, 0.8, True)]
        first = client.post(
            "/api/detect/frame",
            files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
        ).json()
        for _ in range(4):
            client.post(
                "/api/detect/frame",
                files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
                data={"job_id": first["job_id"]},
            )

        stats = client.get(STATISTICS_URL).json()
        assert stats["total_jobs"] == 1
        assert stats["total_detections"] == 5


class TestEmptyDatabase:
    """The dashboard on day zero."""

    def test_every_counter_is_zero(self, client: TestClient) -> None:
        stats = client.get(STATISTICS_URL).json()
        assert stats["total_jobs"] == 0
        assert stats["total_detections"] == 0
        assert stats["unique_plates"] == 0
        assert stats["valid_format_count"] == 0
        assert stats["invalid_format_count"] == 0
        assert stats["unreadable_count"] == 0

    def test_the_averages_are_null_not_zero(self, client: TestClient) -> None:
        """An average confidence of 0 would read as "the model is certain of"""
        stats = client.get(STATISTICS_URL).json()
        assert stats["average_confidence"] is None
        assert stats["average_ocr_confidence"] is None
        assert stats["average_processing_time"] is None

    def test_the_breakdown_still_lists_every_input_type(self, client: TestClient) -> None:
        """A bar chart missing a category looks like a rendering fault."""
        stats = client.get(STATISTICS_URL).json()
        assert {entry["input_type"] for entry in stats["by_input_type"]} == {
            "image",
            "video",
            "webcam",
        }
        assert all(entry["job_count"] == 0 for entry in stats["by_input_type"])


class TestFormatCounters:
    """valid + invalid + unreadable must equal total_detections."""

    def test_the_three_counters_partition_the_detections(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """Defining "invalid" as simply ``is_valid_format = false`` would fold"""
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("51F-22222", "51F22222", 0.9, 0.8, True),
            ("XX-00000", "XXOOOOO", 0.7, 0.5, False),
            (None, None, 0.6, None, False),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["valid_format_count"] == 2
        assert stats["invalid_format_count"] == 1
        assert stats["unreadable_count"] == 1
        assert (
            stats["valid_format_count"] + stats["invalid_format_count"] + stats["unreadable_count"]
            == stats["total_detections"]
        )

    def test_an_unreadable_plate_is_not_counted_as_invalid_format(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [(None, None, 0.6, None, False)]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["unreadable_count"] == 1
        assert stats["invalid_format_count"] == 0

    def test_unique_plates_counts_distinct_text(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """The same plate seen twice is one plate."""
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("51F-11111", "51F11111", 0.8, 0.7, True),
            ("29A1-22222", "29A122222", 0.7, 0.6, True),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["total_detections"] == 3
        assert stats["unique_plates"] == 2


class TestAverages:
    """Means, and the denominators they are taken over."""

    def test_the_detection_average_covers_every_row(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [
            ("51F-11111", "51F11111", 1.0, 0.8, True),
            ("29A1-22222", "29A122222", 0.5, 0.6, True),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["average_confidence"] == pytest.approx(0.75)

    def test_the_ocr_average_excludes_rows_that_read_nothing(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """Counting them as zero would drag the mean down and misreport OCR"""
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.9, 0.6, True),
            (None, None, 0.9, None, False),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert stats["average_ocr_confidence"] == pytest.approx(0.7)

    def test_averages_stay_within_their_declared_bounds(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [("51F-11111", "51F11111", 0.9, 0.8, True)]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        assert 0.0 <= stats["average_confidence"] <= 1.0
        assert 0.0 <= stats["average_ocr_confidence"] <= 1.0
        assert stats["average_processing_time"] >= 0.0


class TestInputTypeBreakdown:
    """Jobs and detections, counted per input type without a join."""

    def test_counts_jobs_and_detections_separately_per_type(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """A join would multiply each job by its detections and count a"""
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
            ("30G-33333", "30G33333", 0.7, 0.6, True),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        by_type = {entry["input_type"]: entry for entry in stats["by_input_type"]}
        assert by_type["image"]["job_count"] == 1
        assert by_type["image"]["detection_count"] == 3
        assert by_type["video"]["job_count"] == 0
        assert by_type["webcam"]["job_count"] == 0

    def test_the_breakdown_totals_agree_with_the_headline_figures(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """Two views of the same data that disagree are worse than either."""
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
        ]
        upload_image(client)
        client.post("/api/detect/frame", files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")})

        stats = client.get(STATISTICS_URL).json()
        assert sum(entry["job_count"] for entry in stats["by_input_type"]) == stats["total_jobs"]
        assert (
            sum(entry["detection_count"] for entry in stats["by_input_type"])
            == stats["total_detections"]
        )

    def test_a_webcam_session_appears_under_its_own_type(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [("51F-11111", "51F11111", 0.9, 0.8, True)]
        client.post("/api/detect/frame", files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")})

        stats = client.get(STATISTICS_URL).json()
        by_type = {entry["input_type"]: entry for entry in stats["by_input_type"]}
        assert by_type["webcam"]["job_count"] == 1
        assert by_type["image"]["job_count"] == 0


class TestDailyTrend:
    """The per-day series behind the trend chart."""

    def test_returns_one_entry_per_requested_day(self, client: TestClient) -> None:
        stats = client.get(STATISTICS_URL, params={"days": 7}).json()
        assert len(stats["daily_counts"]) == 7

    def test_the_series_is_continuous_and_oldest_first(self, client: TestClient) -> None:
        """Days with no activity are zeros, not omissions: a chart fed only the"""
        stats = client.get(STATISTICS_URL, params={"days": 5}).json()
        dates = [dt.date.fromisoformat(entry["date"]) for entry in stats["daily_counts"]]

        assert dates == sorted(dates)
        for earlier, later in zip(dates, dates[1:]):
            assert (later - earlier).days == 1

    def test_the_window_ends_today(self, client: TestClient) -> None:
        stats = client.get(STATISTICS_URL, params={"days": 3}).json()
        last = dt.date.fromisoformat(stats["daily_counts"][-1]["date"])
        assert last == dt.datetime.now(dt.timezone.utc).date()

    def test_todays_upload_lands_on_the_last_day(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
        ]
        upload_image(client)

        stats = client.get(STATISTICS_URL, params={"days": 3}).json()
        today = stats["daily_counts"][-1]
        assert today["job_count"] == 1
        assert today["detection_count"] == 2

    def test_a_quiet_day_reports_zero_rather_than_being_absent(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [("51F-11111", "51F11111", 0.9, 0.8, True)]
        upload_image(client)

        stats = client.get(STATISTICS_URL, params={"days": 5}).json()
        assert all(entry["job_count"] == 0 for entry in stats["daily_counts"][:-1])

    def test_defaults_to_a_sensible_window(self, client: TestClient) -> None:
        stats = client.get(STATISTICS_URL).json()
        assert 1 <= len(stats["daily_counts"]) <= 365

    @pytest.mark.parametrize("days", [0, -1, 366, 10_000])
    def test_an_out_of_range_window_is_refused(self, client: TestClient, days: int) -> None:
        """Unbounded, the response would carry one object per day forever."""
        assert client.get(STATISTICS_URL, params={"days": days}).status_code == 422

    @pytest.mark.parametrize("days", [1, 7, 30, 365])
    def test_accepts_the_documented_range(self, client: TestClient, days: int) -> None:
        response = client.get(STATISTICS_URL, params={"days": days})
        assert response.status_code == 200
        assert len(response.json()["daily_counts"]) == days


class TestHistoricalData:
    """Rows dated in the past, inserted directly."""

    @pytest.fixture()
    def old_and_new(self, db: Session) -> None:
        """One upload from ten days ago and one from today."""
        now = dt.datetime.now(dt.timezone.utc)
        for offset in (10, 0):
            job = DetectionJob(
                input_type=InputType.IMAGE.value,
                status="completed",
                progress=1.0,
                created_at=now - dt.timedelta(days=offset),
            )
            db.add(job)
            db.flush()
            db.add(
                DetectionHistory(
                    plate_number=f"51F-{offset:05d}",
                    raw_ocr_text=f"51F{offset:05d}",
                    confidence=0.9,
                    ocr_confidence=0.8,
                    input_type=InputType.IMAGE.value,
                    bbox_x=1,
                    bbox_y=1,
                    bbox_w=10,
                    bbox_h=10,
                    is_valid_format=True,
                    plate_line_count=1,
                    processing_time=0.3,
                    detected_time=now - dt.timedelta(days=offset),
                    source_job_id=job.id,
                )
            )
        db.commit()

    def test_the_totals_cover_all_time_regardless_of_the_window(
        self, client: TestClient, old_and_new: None
    ) -> None:
        """``days`` bounds the trend series only, not the headline counters."""
        stats = client.get(STATISTICS_URL, params={"days": 3}).json()
        assert stats["total_jobs"] == 2
        assert stats["total_detections"] == 2

    def test_the_today_counters_exclude_the_old_upload(
        self, client: TestClient, old_and_new: None
    ) -> None:
        stats = client.get(STATISTICS_URL).json()
        assert stats["jobs_today"] == 1
        assert stats["detections_today"] == 1

    def test_a_short_window_excludes_the_old_upload_from_the_trend(
        self, client: TestClient, old_and_new: None
    ) -> None:
        stats = client.get(STATISTICS_URL, params={"days": 3}).json()
        assert sum(entry["job_count"] for entry in stats["daily_counts"]) == 1

    def test_a_long_window_includes_it(self, client: TestClient, old_and_new: None) -> None:
        stats = client.get(STATISTICS_URL, params={"days": 30}).json()
        assert sum(entry["job_count"] for entry in stats["daily_counts"]) == 2


class TestResponseShape:
    """The contract the dashboard is built against."""

    def test_carries_every_documented_field(self, client: TestClient) -> None:
        stats = client.get(STATISTICS_URL).json()
        expected = {
            "total_jobs",
            "total_detections",
            "unique_plates",
            "valid_format_count",
            "invalid_format_count",
            "unreadable_count",
            "average_confidence",
            "average_ocr_confidence",
            "average_processing_time",
            "jobs_today",
            "detections_today",
            "by_input_type",
            "daily_counts",
        }
        assert expected <= set(stats)

    def test_the_two_counting_families_are_separate_fields(self, client: TestClient) -> None:
        """A single ``total`` would make the distinction unrepresentable."""
        stats = client.get(STATISTICS_URL).json()
        assert "total_jobs" in stats
        assert "total_detections" in stats

    def test_no_counter_is_ever_negative(self, client: TestClient, pipeline: FakePipeline) -> None:
        pipeline.plates = [("51F-11111", "51F11111", 0.9, 0.8, True)]
        upload_image(client)

        stats = client.get(STATISTICS_URL).json()
        for key, value in stats.items():
            if isinstance(value, int):
                assert value >= 0, f"{key} is negative"
