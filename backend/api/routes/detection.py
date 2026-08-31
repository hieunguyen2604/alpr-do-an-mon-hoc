"""Detection endpoints for image, video, webcam frame, and async background job status."""

from __future__ import annotations

from typing import Annotated, Final

from fastapi import APIRouter, BackgroundTasks, File, Form, Path, UploadFile, status

from backend.api.deps import DbSession, DetectionDep, SettingsDep, StorageDep
from backend.api.routes import ERROR_400, ERROR_404, ERROR_413, ERROR_415, ERROR_500, errors
from backend.core.exceptions import FileTooLargeError, ValidationError
from backend.core.logging import get_logger
from backend.schemas.detection import DetectionJobResponse, DetectionResponse
from backend.services.detection_service import to_job_response

__all__ = ["router"]

logger = get_logger(__name__)

router = APIRouter(tags=["Detection"])

_DETECTION_EXAMPLE: Final[dict[str, object]] = {
    "job_id": "3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840",
    "input_type": "image",
    "results": [
        {
            "plate_number": "51F-12345",
            "raw_ocr_text": "51FI2345",
            "detection_confidence": 0.94,
            "ocr_confidence": 0.87,
            "bbox": {"x": 142, "y": 318, "width": 186, "height": 64},
            "is_valid_format": True,
            "plate_line_count": 1,
            "processing_time": 0.412,
            "plate_image_url": "/files/plates/3f2a1c7e-plate-0.jpg",
        }
    ],
    "plate_count": 1,
    "processing_time": 0.842,
    "image_url": "/files/uploads/9c4f2b1e7a634d8e9f0a1b2c3d4e5f60.jpg",
    "image_width": 1280,
    "image_height": 720,
}

_JOB_EXAMPLE: Final[dict[str, object]] = {
    "id": "3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840",
    "input_type": "video",
    "status": "processing",
    "progress": 0.65,
    "output_url": None,
    "total_frames": 1800,
    "processed_frames": 234,
    "detection_count": 7,
    "created_at": "2026-07-19T09:31:22.145Z",
    "completed_at": None,
}


def _read_upload(file: UploadFile, *, limit_bytes: int) -> bytes:
    """Read an upload into memory, rejecting an oversized one early."""
    if file is None or not file.filename:
        raise ValidationError(
            "Request contained no file part",
            user_message="Vui lòng chọn một tệp để tải lên.",
        )

    declared = getattr(file, "size", None)
    if declared is not None and declared > limit_bytes:
        raise FileTooLargeError.with_limit(
            actual_bytes=int(declared),
            limit_bytes=limit_bytes,
            filename=file.filename,
        )

    # Synchronous read: this endpoint already runs in a worker thread, so
    # blocking here blocks nothing but itself.
    return file.file.read()


@router.post(
    "/detect/image",
    response_model=DetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect and recognize license plates in an image",
    description=(
        "Uploads a single image, runs the full recognition pipeline over it, "
        "stores every plate found and returns them.\n\n"
        "The whole upload is **one job**. An image containing three vehicles "
        "produces three entries in `results`, all sharing the returned "
        "`job_id`, and counts as one upload in the dashboard statistics.\n\n"
        "An image containing **no** plate is a success, not an error: the "
        "response is 200 with an empty `results` list. Reporting it as a 4xx "
        "would remove every negative case from the accuracy figures.\n\n"
        "The file type is determined from the file's magic bytes, not from its "
        "extension or its `Content-Type` header (NFR-S1). A `.jpg` that is "
        "really a ZIP archive is rejected with 415."
    ),
    responses={
        200: {
            "description": "Detection completed. `results` may be empty.",
            "content": {"application/json": {"example": _DETECTION_EXAMPLE}},
        },
        **errors(ERROR_400, ERROR_413, ERROR_415, ERROR_500),
    },
)
def detect_image(
    db: DbSession,
    detection: DetectionDep,
    settings: SettingsDep,
    file: Annotated[
        UploadFile,
        File(description="Image file: JPEG, PNG, WebP or BMP."),
    ],
) -> DetectionResponse:
    """Handle an image upload."""
    payload = _read_upload(file, limit_bytes=settings.max_image_size_bytes)
    return detection.detect_image(db, data=payload, original_filename=file.filename)


@router.post(
    "/detect/video",
    response_model=DetectionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a video for background recognition",
    description=(
        "Accepts a video, stores it and returns **202 Accepted** immediately "
        "with a `job_id`. Processing runs in the background; poll "
        "`GET /api/jobs/{job_id}` for progress and stop once `status` reaches "
        "`completed`, `failed` or `cancelled`.\n\n"
        "The work is not done inline because it cannot be: roughly 200 seconds "
        "of CPU per 60 seconds of footage (NFR-SC3), which no HTTP client or "
        "proxy will wait for. A synchronous endpoint would time out mid-job "
        "with the work half done and no way to learn how it ended.\n\n"
        "Frames are sampled rather than processed exhaustively, and repeated "
        "sightings of the same plate are merged into a single history record "
        "before anything is written — one plate seen in forty frames was still "
        "one plate. Unreadable fragments (a box OCR got no complete string "
        "from) are dropped rather than stored, and two readings that differ "
        "by a single character within a two-second window are folded into "
        "the better-evidenced spelling, so one vehicle does not fan out into "
        "several near-identical rows."
    ),
    responses={
        202: {
            "description": "The video was accepted and queued.",
            "content": {
                "application/json": {
                    "example": {
                        **_JOB_EXAMPLE,
                        "status": "pending",
                        "progress": 0.0,
                        "total_frames": None,
                        "processed_frames": 0,
                        "detection_count": 0,
                    }
                }
            },
        },
        **errors(ERROR_400, ERROR_413, ERROR_415, ERROR_500),
    },
)
def detect_video(
    db: DbSession,
    detection: DetectionDep,
    storage: StorageDep,
    settings: SettingsDep,
    background: BackgroundTasks,
    file: Annotated[
        UploadFile,
        File(description="Video file: MP4, AVI, MOV or MKV."),
    ],
) -> DetectionJobResponse:
    """Accept a video upload and queue it for processing."""
    payload = _read_upload(file, limit_bytes=settings.max_video_size_bytes)
    job = detection.create_video_job(db, data=payload, original_filename=file.filename)

    # Queued rather than awaited. The task opens its own session and its own
    # log context, because this request's session closes as soon as the 202 is
    # written -- long before the job finishes.
    background.add_task(detection.process_video_job, job.id)

    return to_job_response(job, storage)


@router.post(
    "/detect/frame",
    response_model=DetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect license plates in a single webcam frame",
    description=(
        "Processes one frame captured from a webcam and returns the plates "
        "found in it. Intended to be called repeatedly while a live session is "
        "running.\n\n"
        "**Pass the `job_id` back.** The first call omits it and receives a "
        "new one; every later call in the same session must send it, so that "
        "the frames accumulate against one job. Omitting it starts a new "
        "session per frame, which would count a thirty-second capture as "
        "hundreds of uploads and make the usage statistics meaningless.\n\n"
        "Frames are **not stored**. A session produces several nearly identical "
        "frames per second and keeping them would fill the disk to record "
        "nothing; only the cropped plate images are saved, since those are what "
        "a user reviews afterwards."
    ),
    responses={
        200: {
            "description": "The frame was processed. `results` may be empty.",
            "content": {
                "application/json": {
                    "example": {
                        **_DETECTION_EXAMPLE,
                        "input_type": "webcam",
                        "image_url": None,
                    }
                }
            },
        },
        **errors(ERROR_400, ERROR_413, ERROR_415, ERROR_500),
    },
)
def detect_frame(
    db: DbSession,
    detection: DetectionDep,
    settings: SettingsDep,
    file: Annotated[
        UploadFile,
        File(description="A single captured frame, encoded as JPEG or PNG."),
    ],
    job_id: Annotated[
        str | None,
        Form(
            description=(
                "Identifier of the ongoing webcam session, as returned by the "
                "first frame. Omit it on the first call. An unknown or already "
                "finished identifier silently starts a new session rather than "
                "failing, so a page reload does not break the capture."
            ),
            examples=["3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840"],
        ),
    ] = None,
    read_text: Annotated[
        bool,
        Form(
            description=(
                "Whether to read the characters. Send `false` to locate the "
                "plates without reading them, which is roughly twice as fast: "
                "detection costs about 225 ms per frame against 274 ms for OCR "
                "on a 960x540 frame holding three plates.\n\n"
                "Intended for a live preview that tracks boxes between frames "
                "and therefore only needs to read each plate once. Frames sent "
                "this way are **not stored** — a box with no characters is not "
                "a detection record, and a preview would otherwise write "
                "several empty rows per second."
            ),
        ),
    ] = True,
) -> DetectionResponse:
    """Handle one webcam frame."""
    payload = _read_upload(file, limit_bytes=settings.max_image_size_bytes)
    return detection.detect_frame(db, data=payload, job_id=job_id, read_text=read_text)


@router.get(
    "/jobs/{job_id}",
    response_model=DetectionJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the status and progress of a job",
    description=(
        "Returns the current state of an upload or capture session. This is "
        "the endpoint a client polls after `POST /api/detect/video` returns "
        "202.\n\n"
        "`progress` runs from 0.0 to 1.0. Stop polling once `status` is one of "
        "`completed`, `failed` or `cancelled` — those are terminal and nothing "
        "further will change.\n\n"
        "A failed job reports only that it failed. The technical reason is "
        "written to the server log under the request's `request_id` and is "
        "never returned here (NFR-S4)."
    ),
    responses={
        200: {
            "description": "The job's current state.",
            "content": {"application/json": {"example": _JOB_EXAMPLE}},
        },
        **errors(ERROR_404, ERROR_500),
    },
)
def get_job(
    db: DbSession,
    detection: DetectionDep,
    job_id: Annotated[
        str,
        Path(
            description="Job identifier returned when the upload was accepted.",
            examples=["3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840"],
        ),
    ],
) -> DetectionJobResponse:
    """Return one job's progress."""
    return detection.get_job(db, job_id)
