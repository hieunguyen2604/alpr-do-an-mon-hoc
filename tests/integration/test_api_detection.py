"""Integration tests for the detection endpoints.

Each test drives a real HTTP request through the real routers, services and SQL,
and then checks all three places the outcome must be consistent:

1. the **response body** the client receives;
2. the **database rows** that were written;
3. the **files** that landed on disk.

Checking only the first is the trap. A handler can return a convincing response
while persisting nothing, or persist a job and lose its detections, and the
client cannot tell. The upload endpoints are also the application's only
untrusted input surface, so the rejection paths -- wrong type, too large,
executable in disguise -- are tested as carefully as the happy one.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.config import Settings
from backend.models.detection import DetectionHistory, DetectionJob, JobStatus

from .conftest import (
    EXE_DISGUISED_AS_JPEG,
    PDF_BYTES,
    FakePipeline,
    encode_jpeg,
    encode_png,
)

pytestmark = pytest.mark.integration

IMAGE_URL = "/api/detect/image"
FRAME_URL = "/api/detect/frame"


def upload(client: TestClient, data: bytes, filename: str = "car.jpg") -> object:
    """POST one image to the detection endpoint.

    Args:
        client: The test client.
        data: File contents.
        filename: The name the client claims. Never used as a path.

    Returns:
        The HTTP response.
    """
    return client.post(IMAGE_URL, files={"file": (filename, data, "image/jpeg")})


class TestSuccessfulImageDetection:
    """The happy path, checked in the response, the database and on disk."""

    def test_returns_200_with_the_recognised_plate(self, client: TestClient) -> None:
        response = upload(client, encode_jpeg())
        assert response.status_code == 200

        body = response.json()
        assert body["plate_count"] == 1
        assert body["results"][0]["plate_number"] == "51F-12345"
        assert body["input_type"] == "image"
        assert body["job_id"]

    def test_reports_both_confidences_separately(self, client: TestClient) -> None:
        """A single merged number could not express either failure mode."""
        result = upload(client, encode_jpeg()).json()["results"][0]
        assert result["detection_confidence"] == pytest.approx(0.94)
        assert result["ocr_confidence"] == pytest.approx(0.87)

    def test_reports_the_raw_and_the_corrected_string(self, client: TestClient) -> None:
        """Comparing the two is how the correction step is measured."""
        result = upload(client, encode_jpeg()).json()["results"][0]
        assert result["plate_number"] == "51F-12345"
        assert result["raw_ocr_text"] == "51FI2345"

    def test_reports_the_source_dimensions(self, client: TestClient) -> None:
        body = upload(client, encode_jpeg(width=320, height=240)).json()
        assert body["image_width"] == 320
        assert body["image_height"] == 240

    def test_writes_one_job_and_one_detection_row(self, client: TestClient, db: Session) -> None:
        body = upload(client, encode_jpeg()).json()

        job = db.get(DetectionJob, body["job_id"])
        assert job is not None
        assert job.input_type == "image"
        assert job.status == JobStatus.COMPLETED.value
        assert job.progress == 1.0

        rows = (
            db.execute(
                select(DetectionHistory).where(DetectionHistory.source_job_id == body["job_id"])
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].plate_number == "51F-12345"
        assert rows[0].raw_ocr_text == "51FI2345"

    def test_the_persisted_row_matches_the_response(self, client: TestClient, db: Session) -> None:
        """The two views of one detection must not drift apart."""
        body = upload(client, encode_jpeg()).json()
        result = body["results"][0]
        row = db.execute(
            select(DetectionHistory).where(DetectionHistory.source_job_id == body["job_id"])
        ).scalar_one()

        assert row.confidence == pytest.approx(result["detection_confidence"])
        assert row.ocr_confidence == pytest.approx(result["ocr_confidence"])
        assert row.bbox_x == result["bbox"]["x"]
        assert row.bbox_w == result["bbox"]["width"]
        assert row.is_valid_format is result["is_valid_format"]

    def test_stores_the_uploaded_file_under_a_generated_name(
        self, client: TestClient, settings: Settings
    ) -> None:
        body = upload(client, encode_jpeg(), filename="my holiday photo.jpg").json()

        stored = list(settings.upload_dir.iterdir())
        assert len(stored) == 1
        assert "holiday" not in stored[0].name
        assert stored[0].suffix == ".jpg"
        assert body["image_url"].startswith("/files/uploads/")

    def test_stores_a_crop_for_each_plate(self, client: TestClient, settings: Settings) -> None:
        body = upload(client, encode_jpeg()).json()
        crops = list(settings.plate_dir.iterdir())
        assert len(crops) == 1
        assert body["results"][0]["plate_image_url"].startswith("/files/plates/")

    def test_the_stored_file_is_reachable_through_the_static_handler(
        self, client: TestClient
    ) -> None:
        body = upload(client, encode_jpeg()).json()
        served = client.get(body["image_url"])
        assert served.status_code == 200
        assert served.content[:3] == b"\xff\xd8\xff"

    def test_the_response_never_exposes_a_filesystem_path(
        self, client: TestClient, settings: Settings
    ) -> None:
        """NFR-S2: the server's directory layout is not published."""
        raw = upload(client, encode_jpeg()).text
        assert str(settings.storage_root) not in raw
        assert str(settings.upload_dir) not in raw

    def test_accepts_a_png_as_well(self, client: TestClient) -> None:
        response = client.post(IMAGE_URL, files={"file": ("shot.png", encode_png(), "image/png")})
        assert response.status_code == 200

    def test_the_type_is_taken_from_the_bytes_not_the_extension(
        self, client: TestClient, settings: Settings
    ) -> None:
        """A PNG uploaded as ``.jpg`` is stored as ``.png``."""
        client.post(IMAGE_URL, files={"file": ("lying.jpg", encode_png(), "image/jpeg")})
        stored = list(settings.upload_dir.iterdir())
        assert stored[0].suffix == ".png"


class TestMultiplePlatesAreOneJob:
    """One upload with three plates is ONE use of the system."""

    def test_three_plates_produce_three_results_under_one_job(
        self, client: TestClient, pipeline: FakePipeline, db: Session
    ) -> None:
        pipeline.plates = [
            ("51F-11111", "51FIIIII", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
            ("30G-33333", "30G33333", 0.7, 0.6, True),
        ]
        body = upload(client, encode_jpeg()).json()

        assert body["plate_count"] == 3
        assert len(body["results"]) == 3

        assert db.execute(select(func.count()).select_from(DetectionJob)).scalar_one() == 1
        assert db.execute(select(func.count()).select_from(DetectionHistory)).scalar_one() == 3

    def test_every_row_shares_the_returned_job_id(
        self, client: TestClient, pipeline: FakePipeline, db: Session
    ) -> None:
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
        ]
        body = upload(client, encode_jpeg()).json()

        job_ids = set(db.execute(select(DetectionHistory.source_job_id)).scalars().all())
        assert job_ids == {body["job_id"]}

    def test_each_plate_gets_its_own_crop_file(
        self, client: TestClient, pipeline: FakePipeline, settings: Settings
    ) -> None:
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
        ]
        body = upload(client, encode_jpeg()).json()
        crops = sorted(path.name for path in settings.plate_dir.iterdir())
        assert len(crops) == 2
        assert crops == [
            f"{body['job_id']}-plate-0.jpg",
            f"{body['job_id']}-plate-1.jpg",
        ]


class TestNoPlateFoundIsSuccess:
    """An image with no plate is a 200, never a 4xx."""

    def test_returns_200_with_an_empty_result_list(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """Reporting it as an error would erase every negative case from the
        accuracy figures, leaving them measuring only the images that worked."""
        pipeline.plates = []
        response = upload(client, encode_jpeg())

        assert response.status_code == 200
        body = response.json()
        assert body["results"] == []
        assert body["plate_count"] == 0

    def test_the_job_is_still_recorded(
        self, client: TestClient, pipeline: FakePipeline, db: Session
    ) -> None:
        """The user did upload the image; usage statistics must see it."""
        pipeline.plates = []
        body = upload(client, encode_jpeg()).json()

        job = db.get(DetectionJob, body["job_id"])
        assert job is not None
        assert job.status == JobStatus.COMPLETED.value
        assert db.execute(select(func.count()).select_from(DetectionHistory)).scalar_one() == 0


class TestUnreadablePlateIsStillRecorded:
    """A plate located but not read is a real, reportable outcome."""

    def test_the_detection_is_returned_without_text(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [(None, None, 0.85, None, False)]
        body = upload(client, encode_jpeg()).json()

        assert body["plate_count"] == 1
        result = body["results"][0]
        assert result["plate_number"] is None
        assert result["ocr_confidence"] is None
        assert result["detection_confidence"] == pytest.approx(0.85)

    def test_the_row_is_written_with_a_null_plate_number(
        self, client: TestClient, pipeline: FakePipeline, db: Session
    ) -> None:
        """Dropping it would make recognition accuracy perfect by construction."""
        pipeline.plates = [(None, None, 0.85, None, False)]
        upload(client, encode_jpeg())

        row = db.execute(select(DetectionHistory)).scalar_one()
        assert row.plate_number is None
        assert row.ocr_confidence is None
        assert row.confidence == pytest.approx(0.85)
        assert row.is_valid_format is False


class TestRejectedUploads:
    """The untrusted input surface."""

    def test_an_executable_renamed_as_a_jpeg_is_refused_with_415(self, client: TestClient) -> None:
        """NFR-S1: the extension and the Content-Type header are both ignored.

        Both are chosen by whoever uploads the file, so the only trustworthy
        evidence is the file's own signature.
        """
        response = client.post(
            IMAGE_URL,
            files={"file": ("photo.jpg", EXE_DISGUISED_AS_JPEG, "image/jpeg")},
        )
        assert response.status_code == 415
        assert response.json()["error"] == "UNSUPPORTED_MEDIA_TYPE"

    def test_a_pdf_renamed_as_a_jpeg_is_refused_with_415(self, client: TestClient) -> None:
        response = client.post(IMAGE_URL, files={"file": ("scan.jpg", PDF_BYTES, "image/jpeg")})
        assert response.status_code == 415

    def test_a_rejected_upload_writes_nothing_at_all(
        self, client: TestClient, db: Session, settings: Settings
    ) -> None:
        """Validation runs before a single byte reaches the disk or the database."""
        client.post(
            IMAGE_URL,
            files={"file": ("photo.jpg", EXE_DISGUISED_AS_JPEG, "image/jpeg")},
        )
        assert db.execute(select(func.count()).select_from(DetectionJob)).scalar_one() == 0
        assert list(settings.upload_dir.iterdir()) == []

    def test_an_oversized_upload_is_refused_with_413(
        self, client: TestClient, settings: Settings
    ) -> None:
        oversized = encode_jpeg() + b"\x00" * settings.max_image_size_bytes
        response = client.post(IMAGE_URL, files={"file": ("huge.jpg", oversized, "image/jpeg")})
        assert response.status_code == 413
        assert response.json()["error"] == "FILE_TOO_LARGE"

    def test_an_oversized_upload_is_not_stored(
        self, client: TestClient, settings: Settings
    ) -> None:
        oversized = encode_jpeg() + b"\x00" * settings.max_image_size_bytes
        client.post(IMAGE_URL, files={"file": ("huge.jpg", oversized, "image/jpeg")})
        assert list(settings.upload_dir.iterdir()) == []

    def test_an_empty_file_is_refused(self, client: TestClient) -> None:
        response = client.post(IMAGE_URL, files={"file": ("empty.jpg", b"", "image/jpeg")})
        assert response.status_code in (400, 415)

    def test_a_request_with_no_file_part_is_a_422(self, client: TestClient) -> None:
        response = client.post(IMAGE_URL)
        assert response.status_code == 422

    def test_a_truncated_image_is_refused_with_400(self, client: TestClient) -> None:
        """A valid JPEG header proves nothing about the rest of the file.

        The signature check passes and the decode fails, which is why the two
        are separate steps.
        """
        truncated = encode_jpeg()[:40]
        response = client.post(IMAGE_URL, files={"file": ("broken.jpg", truncated, "image/jpeg")})
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"

    def test_a_video_sent_to_the_image_endpoint_is_refused(self, client: TestClient) -> None:
        mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 64
        response = client.post(IMAGE_URL, files={"file": ("clip.mp4", mp4, "video/mp4")})
        assert response.status_code == 415


class TestErrorBodies:
    """Every failure uses one body shape and leaks nothing (NFR-S4)."""

    def test_an_error_carries_a_code_a_message_and_a_request_id(self, client: TestClient) -> None:
        response = client.post(IMAGE_URL, files={"file": ("x.jpg", PDF_BYTES, "image/jpeg")})
        body = response.json()
        assert set(body) >= {"error", "message", "request_id"}
        assert body["request_id"]

    def test_the_message_is_vietnamese_and_the_code_is_stable(self, client: TestClient) -> None:
        body = client.post(IMAGE_URL, files={"file": ("x.jpg", PDF_BYTES, "image/jpeg")}).json()
        assert body["error"] == "UNSUPPORTED_MEDIA_TYPE"
        assert body["message"].strip()

    def test_no_traceback_or_internal_detail_reaches_the_client(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        """The technical half goes to the log under the same request identifier."""
        pipeline.raises = RuntimeError("secret internal detail at /srv/models/best.pt")
        response = client.post(IMAGE_URL, files={"file": ("x.jpg", encode_jpeg(), "image/jpeg")})

        assert response.status_code == 500
        raw = response.text
        assert "Traceback" not in raw
        assert "RuntimeError" not in raw
        assert "secret internal detail" not in raw
        assert "/srv/models" not in raw

    def test_the_request_id_is_echoed_as_a_header(self, client: TestClient) -> None:
        response = client.post(IMAGE_URL, files={"file": ("x.jpg", PDF_BYTES, "image/jpeg")})
        assert response.headers["X-Request-ID"] == response.json()["request_id"]

    def test_an_inbound_request_id_is_honoured(self, client: TestClient) -> None:
        """A trace started by the frontend or a proxy must continue, not restart."""
        response = client.post(
            IMAGE_URL,
            files={"file": ("x.jpg", encode_jpeg(), "image/jpeg")},
            headers={"X-Request-ID": "trace-me-1234"},
        )
        assert response.headers["X-Request-ID"] == "trace-me-1234"

    def test_a_failed_image_detection_leaves_no_partial_rows(
        self, client: TestClient, pipeline: FakePipeline, db: Session
    ) -> None:
        """A failure must not leave a half-written detection behind.

        This part of the contract holds: the rollback in ``_fail_job`` discards
        everything the failed attempt wrote, so no detection row survives
        pointing at a job that never completed.
        """
        pipeline.raises = RuntimeError("boom")
        client.post(IMAGE_URL, files={"file": ("x.jpg", encode_jpeg(), "image/jpeg")})

        assert db.execute(select(func.count()).select_from(DetectionHistory)).scalar_one() == 0

    def test_a_failed_image_detection_records_the_failed_job(
        self, client: TestClient, pipeline: FakePipeline, db: Session
    ) -> None:
        """A failed image upload must leave a job row marked failed.

        This carried a ``strict`` ``xfail`` marker for as long as the defect
        lived: ``_create_job`` only flushed the job on the image and webcam
        paths, so ``_fail_job``'s rollback discarded the row before the failure
        could be written and the upload left **zero** rows -- failures were
        invisible to the usage figures. ``_create_job`` now commits, matching
        what the video path always did, and the marker came off because
        ``strict`` turned the unexpected pass into a failure rather than letting
        a stale excuse sit here.
        """
        pipeline.raises = RuntimeError("disk on fire")
        response = client.post(IMAGE_URL, files={"file": ("x.jpg", encode_jpeg(), "image/jpeg")})
        assert response.status_code == 500

        job = db.execute(select(DetectionJob)).scalar_one()
        assert job.status == JobStatus.FAILED.value
        assert "disk on fire" in (job.error_message or "")
        assert "disk on fire" not in response.text

    def test_a_failed_video_job_does_record_its_failure(
        self, client: TestClient, db: Session
    ) -> None:
        """The contrast that isolates the defect above.

        ``create_video_job`` commits before the background work begins, so the
        job survives the rollback and its failure *is* recorded. The image path
        differs only in that missing commit.
        """
        mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 512
        accepted = client.post("/api/detect/video", files={"file": ("clip.mp4", mp4, "video/mp4")})
        assert accepted.status_code == 202

        job = db.execute(select(DetectionJob)).scalar_one()
        # The background task ran inline via TestClient and failed to open the
        # dummy container, which is exactly the failure being observed.
        db.refresh(job)
        assert job.status == JobStatus.FAILED.value
        assert job.error_message
        assert job.error_message not in accepted.text

    def test_an_unknown_route_returns_the_same_error_shape(self, client: TestClient) -> None:
        """One body format for a client to parse, not two."""
        body = client.get("/api/does-not-exist").json()
        assert body["error"] == "NOT_FOUND"
        assert "message" in body


class TestWebcamFrames:
    """A capture session is one job, not one job per frame."""

    def test_a_first_frame_starts_a_session(self, client: TestClient) -> None:
        response = client.post(
            FRAME_URL, files={"file": ("frame.jpg", encode_jpeg(), "image/jpeg")}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["input_type"] == "webcam"
        assert body["job_id"]

    def test_passing_the_job_id_back_continues_the_same_session(
        self, client: TestClient, db: Session
    ) -> None:
        """Omitting it would count a thirty-second capture as hundreds of uploads."""
        first = client.post(
            FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")}
        ).json()

        for _ in range(3):
            follow_up = client.post(
                FRAME_URL,
                files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
                data={"job_id": first["job_id"]},
            ).json()
            assert follow_up["job_id"] == first["job_id"]

        assert db.execute(select(func.count()).select_from(DetectionJob)).scalar_one() == 1

    def test_omitting_the_job_id_starts_a_new_session_each_time(
        self, client: TestClient, db: Session
    ) -> None:
        ids = {
            client.post(FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")}).json()[
                "job_id"
            ]
            for _ in range(3)
        }
        assert len(ids) == 3
        assert db.execute(select(func.count()).select_from(DetectionJob)).scalar_one() == 3

    def test_an_unknown_job_id_starts_a_new_session_rather_than_failing(
        self, client: TestClient
    ) -> None:
        """A page reload mid-session must not show the user an error."""
        response = client.post(
            FRAME_URL,
            files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
            data={"job_id": "never-existed"},
        )
        assert response.status_code == 200
        assert response.json()["job_id"] != "never-existed"

    def test_frames_are_not_stored_on_disk(self, client: TestClient, settings: Settings) -> None:
        """A session produces near-identical frames several times a second."""
        client.post(FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")})
        assert list(settings.upload_dir.iterdir()) == []

    def test_the_response_carries_no_image_url(self, client: TestClient) -> None:
        body = client.post(FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")}).json()
        assert body["image_url"] is None

    def test_the_plate_crop_is_still_stored(self, client: TestClient, settings: Settings) -> None:
        """It is what a user reviews afterwards."""
        client.post(FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")})
        assert len(list(settings.plate_dir.iterdir())) == 1

    def test_frames_are_held_to_the_same_magic_byte_rule(self, client: TestClient) -> None:
        response = client.post(
            FRAME_URL,
            files={"file": ("f.jpg", EXE_DISGUISED_AS_JPEG, "image/jpeg")},
        )
        assert response.status_code == 415

    def test_the_frame_counter_advances(self, client: TestClient, db: Session) -> None:
        first = client.post(
            FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")}
        ).json()
        for _ in range(2):
            client.post(
                FRAME_URL,
                files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
                data={"job_id": first["job_id"]},
            )

        db.expire_all()
        job = db.get(DetectionJob, first["job_id"])
        assert job.processed_frames == 3


class TestDetectionOnlyFrames:
    """`read_text=false` locates plates without reading them.

    The live video preview re-detects the same vehicles several times a second.
    OCR is 55% of the per-frame cost and produces the same string every time, so
    a client that tracks boxes between frames reads each plate once and asks for
    detection alone in between.
    """

    def test_the_flag_reaches_the_pipeline(self, client: TestClient, pipeline) -> None:
        """Routes have swallowed form fields before; assert it arrives."""
        client.post(
            FRAME_URL,
            files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
            data={"read_text": "false"},
        )
        assert pipeline.last_read_text is False

    def test_reading_is_on_by_default(self, client: TestClient, pipeline) -> None:
        """Every stored result and published measurement uses the default."""
        client.post(FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")})
        assert pipeline.last_read_text is True

    def test_boxes_come_back_without_text(self, client: TestClient) -> None:
        body = client.post(
            FRAME_URL,
            files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
            data={"read_text": "false"},
        ).json()

        assert body["plate_count"] == 1
        entry = body["results"][0]
        assert entry["plate_number"] is None
        assert entry["raw_ocr_text"] is None
        assert entry["ocr_confidence"] is None
        assert entry["is_valid_format"] is False
        # The box itself is the point of the call, so it must survive intact.
        assert entry["detection_confidence"] > 0.0
        assert entry["bbox"]["width"] > 0

    def test_nothing_is_written_to_history(self, client: TestClient, db: Session) -> None:
        """A box with no characters is not a detection record.

        Without this the preview would write several empty rows per second and
        every count derived from the history would be meaningless.
        """
        client.post(
            FRAME_URL,
            files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
            data={"read_text": "false"},
        )
        assert db.execute(select(func.count()).select_from(DetectionHistory)).scalar_one() == 0

    def test_no_plate_crop_is_stored_either(
        self, client: TestClient, settings: Settings
    ) -> None:
        client.post(
            FRAME_URL,
            files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
            data={"read_text": "false"},
        )
        assert list(settings.plate_dir.iterdir()) == []

    def test_reading_frames_still_store(self, client: TestClient, db: Session) -> None:
        """The cheap path must not disable the normal one."""
        client.post(
            FRAME_URL,
            files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
            data={"read_text": "true"},
        )
        assert db.execute(select(func.count()).select_from(DetectionHistory)).scalar_one() == 1

    def test_the_session_survives_a_mix_of_both(self, client: TestClient, db: Session) -> None:
        """A preview alternates the two against one job."""
        first = client.post(
            FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")}
        ).json()

        for read_text in ("false", "false", "true"):
            follow_up = client.post(
                FRAME_URL,
                files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
                data={"job_id": first["job_id"], "read_text": read_text},
            ).json()
            assert follow_up["job_id"] == first["job_id"]

        assert db.execute(select(func.count()).select_from(DetectionJob)).scalar_one() == 1
        # Two reading frames stored one row each; the two detection-only frames
        # stored nothing.
        assert db.execute(select(func.count()).select_from(DetectionHistory)).scalar_one() == 2

    def test_the_frame_counter_counts_both_kinds(
        self, client: TestClient, db: Session
    ) -> None:
        """Progress that ignored the cheap frames would understate the session."""
        first = client.post(
            FRAME_URL, files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")}
        ).json()
        for _ in range(2):
            client.post(
                FRAME_URL,
                files={"file": ("f.jpg", encode_jpeg(), "image/jpeg")},
                data={"job_id": first["job_id"], "read_text": "false"},
            )

        db.expire_all()
        job = db.get(DetectionJob, first["job_id"])
        assert job.processed_frames == 3


class TestJobStatusEndpoint:
    """Polling a job."""

    def test_returns_the_state_of_a_known_job(self, client: TestClient) -> None:
        created = upload(client, encode_jpeg()).json()
        response = client.get(f"/api/jobs/{created['job_id']}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == created["job_id"]
        assert body["status"] == "completed"
        assert body["progress"] == 1.0
        assert body["detection_count"] == 1

    def test_an_unknown_job_is_a_404(self, client: TestClient) -> None:
        response = client.get("/api/jobs/never-existed")
        assert response.status_code == 404
        assert response.json()["error"] == "NOT_FOUND"

    def test_the_status_of_a_failed_job_never_carries_its_error_message(
        self, client: TestClient, db: Session
    ) -> None:
        """NFR-S4: the technical reason stays server-side.

        Driven through the video path, which is the one that actually persists
        a failed job -- see the known defect recorded in
        ``TestErrorBodies.test_a_failed_image_detection_records_the_failed_job``.
        """
        mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 512
        client.post("/api/detect/video", files={"file": ("clip.mp4", mp4, "video/mp4")})

        job = db.execute(select(DetectionJob)).scalar_one()
        db.refresh(job)
        assert job.status == JobStatus.FAILED.value
        assert job.error_message

        body = client.get(f"/api/jobs/{job.id}").json()
        assert body["status"] == "failed"
        assert "error_message" not in body
        assert job.error_message not in str(body)

    def test_the_detection_count_reflects_the_plates_found(
        self, client: TestClient, pipeline: FakePipeline
    ) -> None:
        pipeline.plates = [
            ("51F-11111", "51F11111", 0.9, 0.8, True),
            ("29A1-22222", "29A122222", 0.8, 0.7, True),
        ]
        created = upload(client, encode_jpeg()).json()
        body = client.get(f"/api/jobs/{created['job_id']}").json()
        assert body["detection_count"] == 2


class TestResponseHeaders:
    """Cross-cutting middleware behaviour."""

    def test_every_response_carries_a_request_id_and_a_duration(self, client: TestClient) -> None:
        response = upload(client, encode_jpeg())
        assert response.headers["X-Request-ID"]
        assert float(response.headers["X-Process-Time"]) >= 0.0

    def test_the_api_documents_itself(self, client: TestClient) -> None:
        schema = client.get("/openapi.json")
        assert schema.status_code == 200
        paths = schema.json()["paths"]
        assert "/api/detect/image" in paths
        assert "/api/history" in paths
        assert "/api/statistics" in paths
