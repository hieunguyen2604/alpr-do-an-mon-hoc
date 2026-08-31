"""Pydantic v2 schemas: API wire contract, request/response models, and OpenAPI schema."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

__all__ = [
    "BoundingBoxSchema",
    "DetectionResultSchema",
    "DetectionResponse",
    "DetectionHistoryResponse",
    "DetectionJobResponse",
    "HistoryListResponse",
    "InputTypeCountSchema",
    "DailyCountSchema",
    "StatisticsResponse",
    "HealthResponse",
    "ErrorResponse",
]

InputTypeLiteral = Literal["image", "video", "webcam"]
"""Accepted input types. A ``Literal`` renders in Swagger as a dropdown of the
valid values and is validated automatically, unlike a free-form string."""

JobStatusLiteral = Literal["pending", "processing", "completed", "failed", "cancelled"]
"""Job lifecycle states, as documented on
:class:`~backend.models.detection.JobStatus`."""

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
"""A probability in ``[0.0, 1.0]``. Named so the bound is stated once."""


class BoundingBoxSchema(BaseModel):
    """Location of a detected plate within its source image.

    Uses the ``x, y, width, height`` form with the origin at the top-left
    corner -- the same convention as OpenCV, as the database columns, and as
    the HTML canvas the frontend draws on. Keeping one convention end to end
    removes the coordinate conversion that would otherwise sit at each
    boundary, and with it the chance of getting one of them wrong.
    """

    model_config = ConfigDict(from_attributes=True)

    x: int = Field(
        ...,
        ge=0,
        description="Left edge of the box in pixels, measured from the image's left side.",
        examples=[142],
    )
    y: int = Field(
        ...,
        ge=0,
        description="Top edge of the box in pixels, measured from the image's top side.",
        examples=[318],
    )
    width: int = Field(..., gt=0, description="Width of the box in pixels.", examples=[186])
    height: int = Field(..., gt=0, description="Height of the box in pixels.", examples=[64])


class DetectionResultSchema(BaseModel):
    """A single plate found during one detection run.

    Returned inside the response to an image, frame or video request. The two
    confidence values are separate fields on purpose: a low
    ``detection_confidence`` means the model was unsure it was looking at a
    plate at all, while a low ``ocr_confidence`` means it was sure of the plate
    but unsure of the characters. Merging them into one number would make those
    two very different failures indistinguishable in the results.
    """

    model_config = ConfigDict(from_attributes=True)

    plate_number: str | None = Field(
        default=None,
        description=(
            "Recognized license plate text after normalization and regex "
            "correction. Null when OCR could not read the plate; the detection "
            "is still reported."
        ),
        examples=["51F-12345"],
    )
    raw_ocr_text: str | None = Field(
        default=None,
        description=(
            "Unmodified text returned by the OCR engine before any correction. "
            "Exposed so the effect of post-processing can be measured against "
            "'plate_number'."
        ),
        examples=["51FI2345"],
    )
    detection_confidence: Confidence = Field(
        ...,
        description="Confidence of the plate DETECTION step (object detector), from 0 to 1.",
        examples=[0.94],
    )
    ocr_confidence: Confidence | None = Field(
        default=None,
        description=(
            "Confidence of the OCR step, from 0 to 1. Reported separately from "
            "the detection confidence. Null when no text was read."
        ),
        examples=[0.87],
    )
    bbox: BoundingBoxSchema = Field(
        ..., description="Position of the plate within the source image."
    )
    is_valid_format: bool = Field(
        default=False,
        description=(
            "Whether the recognized text matches a known **civil** Vietnamese "
            "plate format. False flags the result rather than discarding it. "
            "Read this together with `plate_kind`: an army plate is a genuine "
            "plate that is deliberately reported as false, because it lies "
            "outside the civil registration system. Presenting such a result as "
            "'wrong format' misrepresents it."
        ),
    )
    plate_kind: str | None = Field(
        default=None,
        description=(
            "Plate family inferred from the character string: `car`, "
            "`motorcycle_new`, `motorcycle_old`, `blue_car`, `blue_motorcycle`, "
            "`special`, `diplomatic`, `military`, `unknown`. Note what this "
            "cannot see: a commercial vehicle's yellow plate carries the same "
            "layout as a private vehicle's white one, so both report `car`. "
            "Use `plate_color` to separate them."
        ),
        examples=["car"],
    )
    plate_color: str | None = Field(
        default=None,
        description=(
            "Background colour read from the cropped image: `white`, `yellow`, "
            "`blue`, `red`, or `unknown`. Per Circular 79/2024/TT-BCA: white = "
            "private/business entity, yellow = commercial transport, blue = "
            "state agency, red = army. Complements `plate_kind` rather than "
            "replacing it -- a diplomatic plate has a white background like a "
            "private one, and only its string reveals what it is."
        ),
        examples=["yellow"],
    )
    plate_color_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Fraction of sampled pixels supporting `plate_color`. Not a "
            "probability: it is the margin the colour decision rests on."
        ),
        examples=[0.69],
    )
    plate_display: str | None = Field(
        default=None,
        description=(
            "Plate number rendered with the separators the physical plate "
            "carries, e.g. `29E-015.66` for `29E01566`. Provided for display "
            "only -- search, comparison and accuracy measurement all use the "
            "bare `plate_number`."
        ),
        examples=["29E-015.66"],
    )
    video_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Where in the source clip this plate was found, in seconds. `null` "
            "for images and realtime frames, which have no timeline, and for "
            "rows written before migration `0003`. A timestamp rather than a "
            "frame index: an index means nothing without the clip's frame rate."
        ),
        examples=[12.4],
    )
    plate_line_count: int | None = Field(
        default=None,
        ge=1,
        le=2,
        description="Number of text lines on the plate: 1 for single-line, 2 for two-line.",
        examples=[1],
    )
    processing_time: float = Field(
        default=0.0,
        ge=0.0,
        description="Seconds spent processing this plate, detection plus OCR.",
        examples=[0.412],
    )
    plate_image_url: str | None = Field(
        default=None,
        description="URL of the cropped plate image, or null when no crop was stored.",
        examples=["/api/files/plates/9f2c-plate-0.jpg"],
    )


class DetectionResponse(BaseModel):
    """The outcome of one synchronous detection: an image upload or a frame.

    Wraps the per-plate results rather than returning a bare list, for two
    reasons that only show up later. ``job_id`` is what groups these plates as
    one upload -- without it the client cannot ask about them again, and a
    webcam client cannot tell the server that its next frame belongs to the
    same session. And a JSON *object* can gain a field in a later version,
    whereas a top-level array cannot without breaking every consumer.

    An image containing no plate is a **successful** response with an empty
    ``results`` list and HTTP 200, never a 4xx: treating "found nothing" as an
    error would erase every negative case from the statistics and leave the
    reported accuracy measuring only the images that happened to work.
    """

    model_config = ConfigDict(from_attributes=True)

    job_id: str = Field(
        ...,
        description=(
            "Identifier of the job that produced these results. All plates "
            "found in one upload share it. Pass it back on the next webcam "
            "frame to continue the same session."
        ),
        examples=["3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840"],
    )
    input_type: InputTypeLiteral = Field(
        ..., description="Source of this detection: image, video or webcam."
    )
    results: list[DetectionResultSchema] = Field(
        default_factory=list,
        description=(
            "One entry per license plate found. Empty when the image contains "
            "no plate, which is a normal successful outcome."
        ),
    )
    plate_count: int = Field(
        ..., ge=0, description="Number of plates found, i.e. the length of 'results'."
    )
    processing_time: float = Field(
        ...,
        ge=0.0,
        description=(
            "Total wall-clock seconds for the whole run. Not the sum of the "
            "per-plate times: it also covers decoding and shared preprocessing."
        ),
        examples=[0.842],
    )
    image_url: str | None = Field(
        default=None,
        description=(
            "URL of the stored source image. Null for webcam frames, which are not persisted."
        ),
    )
    image_width: int = Field(default=0, ge=0, description="Width in pixels of the processed image.")
    image_height: int = Field(
        default=0, ge=0, description="Height in pixels of the processed image."
    )


class DetectionHistoryResponse(BaseModel):
    """One stored detection record, as returned by the history endpoints.

    Maps directly from
    :class:`~backend.models.detection.DetectionHistory`. Every field of the
    approved schema is exposed except the raw filesystem paths: those are
    replaced by URLs, so that the server's directory layout is not published to
    the client and files can only be reached through the endpoint that checks
    the request first (NFR-S2).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")
    """``extra="forbid"`` is a guard, not a formality.

    Pydantic's default is to *silently drop* a keyword it does not recognise. A
    mapper that enumerates its fields -- as ``HistoryService._to_response`` does
    -- therefore keeps working after someone adds a field to the schema and
    passes it from the mapper before declaring it here: the value simply never
    reaches the response, on this endpoint only, with nothing raised anywhere.
    That is precisely how ``plate_display`` came back empty on the history
    endpoint while working on the detection one. Forbidding extras turns that
    class of drift into an error at the first request instead of a field the
    interface quietly renders as a dash.
    """

    id: int = Field(..., description="Unique identifier of the detection record.")
    plate_number: str | None = Field(
        default=None,
        description="Normalized license plate text, or null when OCR read nothing.",
        examples=["51F-12345"],
    )
    raw_ocr_text: str | None = Field(
        default=None,
        description="Raw OCR output before correction, kept for accuracy analysis.",
        examples=["51FI2345"],
    )
    confidence: Confidence = Field(
        ..., description="Confidence of the detection step, from 0 to 1."
    )
    ocr_confidence: Confidence | None = Field(
        default=None, description="Confidence of the OCR step, from 0 to 1."
    )
    input_type: InputTypeLiteral = Field(
        ..., description="Source of this detection: image, video or webcam."
    )
    image_path: str | None = Field(
        default=None,
        description="Relative URL of the source image or extracted video frame.",
    )
    plate_image_path: str | None = Field(
        default=None, description="Relative URL of the cropped plate image."
    )
    bbox_x: int = Field(..., description="Left edge of the plate box, in pixels.")
    bbox_y: int = Field(..., description="Top edge of the plate box, in pixels.")
    bbox_w: int = Field(..., description="Width of the plate box, in pixels.")
    bbox_h: int = Field(..., description="Height of the plate box, in pixels.")
    is_valid_format: bool = Field(
        ...,
        description=(
            "Whether the plate text matches a **civil** Vietnamese plate format. "
            "Read together with `plate_kind`: army plates report false by design."
        ),
    )
    plate_kind: str | None = Field(
        default=None,
        description="Plate family inferred from the string, e.g. `car`, `military`.",
        examples=["car"],
    )
    plate_color: str | None = Field(
        default=None,
        description="Background colour read from the crop: `white`, `yellow`, `blue`, `red`.",
        examples=["yellow"],
    )
    plate_color_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Fraction of sampled pixels supporting `plate_color`.",
    )
    plate_display: str | None = Field(
        default=None,
        description=(
            "`plate_number` with the separators the physical plate carries, "
            "e.g. `29E-015.66`. Derived at read time rather than stored, so it "
            "is present on every row including those written before the field "
            "existed. Display only -- search and matching use `plate_number`."
        ),
        examples=["29E-015.66"],
    )
    video_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Where in the source clip this plate was found, in seconds. `null` "
            "for images and realtime frames, which have no timeline, and for "
            "rows written before migration `0003`. A timestamp rather than a "
            "frame index: an index means nothing without the clip's frame rate."
        ),
        examples=[12.4],
    )
    plate_line_count: int | None = Field(
        default=None, description="Number of text lines on the plate: 1 or 2."
    )
    processing_time: float = Field(..., ge=0.0, description="Seconds spent processing this plate.")
    detected_time: dt.datetime = Field(
        ..., description="UTC timestamp of when the plate was detected."
    )
    created_at: dt.datetime = Field(
        ..., description="UTC timestamp of when this record was stored."
    )
    source_job_id: str = Field(
        ...,
        description=(
            "Identifier of the upload that produced this record. Detections "
            "sharing this value came from the same image, video or webcam "
            "session."
        ),
        examples=["3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840"],
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bbox(self) -> BoundingBoxSchema:
        """Return the four bbox columns as a single nested object.

        The columns are flat in the database because that is how the approved
        schema stores them, but a client drawing an overlay wants one object.
        Deriving it here means the response carries both shapes without the
        database having to.
        """
        return BoundingBoxSchema(
            x=self.bbox_x, y=self.bbox_y, width=self.bbox_w, height=self.bbox_h
        )


class DetectionJobResponse(BaseModel):
    """State of one upload or capture session.

    Returned by the video upload endpoint alongside ``202 Accepted``, and by
    the job status endpoint that the frontend polls while processing runs
    (decision AD-02).

    ``error_message`` from the ORM model is intentionally absent: it holds the
    technical failure description, which belongs in the log. A failed job is
    reported to the user through ``status`` plus the generic Vietnamese message
    in :class:`ErrorResponse`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Unique job identifier, used to poll processing status.",
        examples=["3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840"],
    )
    input_type: InputTypeLiteral = Field(
        ..., description="Type of input this job processes: image, video or webcam."
    )
    status: JobStatusLiteral = Field(
        ...,
        description=(
            "Current state. Terminal states are 'completed', 'failed' and "
            "'cancelled'; clients should stop polling once one is reached."
        ),
    )
    progress: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Completion fraction from 0.0 to 1.0, for progress display.",
        examples=[0.65],
    )
    output_url: str | None = Field(
        default=None,
        description=(
            "URL of the annotated image or processed video. Null until the job "
            "completes successfully."
        ),
    )
    total_frames: int | None = Field(
        default=None,
        description="Total frames to process for a video, or null if not applicable.",
    )
    processed_frames: int = Field(default=0, description="Number of frames processed so far.")
    detection_count: int = Field(
        default=0, description="Number of license plates found by this job so far."
    )
    created_at: dt.datetime = Field(..., description="UTC timestamp of when the job was accepted.")
    completed_at: dt.datetime | None = Field(
        default=None,
        description="UTC timestamp of when the job finished, or null if still running.",
    )


class HistoryListResponse(BaseModel):
    """A page of detection records.

    The history table can hold 100 000 rows (NFR-SC2), so results are always
    paginated -- there is no unpaginated variant to reach for by accident.
    ``total`` counts the rows matching the current filters, not the rows in
    this page.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[DetectionHistoryResponse] = Field(
        default_factory=list,
        description="Detection records in this page, newest first by default.",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total records matching the query across all pages.",
        examples=[1247],
    )
    page: int = Field(..., ge=1, description="Current page number, starting at 1.")
    page_size: int = Field(
        ..., ge=1, description="Maximum number of records per page.", examples=[20]
    )
    total_pages: int = Field(
        ..., ge=0, description="Total number of pages available for this query."
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_next(self) -> bool:
        """Return whether a page follows this one."""
        return self.page < self.total_pages

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_previous(self) -> bool:
        """Return whether a page precedes this one."""
        return self.page > 1

    @classmethod
    def build(
        cls,
        *,
        items: list[Any],
        total: int,
        page: int,
        page_size: int,
    ) -> HistoryListResponse:
        """Assemble a page, computing ``total_pages`` from the inputs.

        Keeps the ceiling division in one place. Done at each call site it
        would eventually be written as ``total // page_size`` somewhere and
        drop the final partial page.

        Args:
            items: The ORM rows or dictionaries for this page.
            total: Count of records matching the query, across all pages.
            page: Current page number, 1-based.
            page_size: Maximum records per page.

        Returns:
            A fully populated response.
        """
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        return cls(
            items=[DetectionHistoryResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class InputTypeCountSchema(BaseModel):
    """Usage broken down by one input type."""

    model_config = ConfigDict(from_attributes=True)

    input_type: InputTypeLiteral = Field(..., description="The input type being counted.")
    job_count: int = Field(..., ge=0, description="Number of uploads or sessions of this type.")
    detection_count: int = Field(
        ..., ge=0, description="Number of license plates found across those uploads."
    )


class DailyCountSchema(BaseModel):
    """Activity on a single calendar day, for the dashboard trend chart."""

    model_config = ConfigDict(from_attributes=True)

    date: dt.date = Field(..., description="Calendar date in UTC.", examples=["2026-07-19"])
    job_count: int = Field(..., ge=0, description="Number of uploads on this date.")
    detection_count: int = Field(
        ..., ge=0, description="Number of license plates detected on this date."
    )


class StatisticsResponse(BaseModel):
    """Aggregate figures for the dashboard.

    Two families of counter, kept apart by name because conflating them is the
    single easiest way to publish a wrong number:

    * ``*_jobs`` counts **uploads and sessions** -- how much the system was
      used. One image is one job however many plates it contains.
    * ``*_detections`` counts **license plates** -- how much was recognized.
      One image containing three plates contributes three.

    A dashboard tile labelled "images processed" must read ``total_jobs``. Using
    ``total_detections`` there would inflate the figure by the average number of
    plates per image, and the error would look plausible enough to survive
    review.
    """

    model_config = ConfigDict(from_attributes=True)

    total_jobs: int = Field(
        ...,
        ge=0,
        description=(
            "Total number of uploads and capture sessions. This is the usage "
            "figure: one image containing three plates counts as one."
        ),
        examples=[412],
    )
    total_detections: int = Field(
        ...,
        ge=0,
        description=(
            "Total number of license plates detected. One image containing "
            "three plates contributes three."
        ),
        examples=[689],
    )
    unique_plates: int = Field(
        ..., ge=0, description="Number of distinct license plate numbers recognized."
    )
    valid_format_count: int = Field(
        ...,
        ge=0,
        description="Detections whose text matched a Vietnamese plate format.",
    )
    invalid_format_count: int = Field(
        ...,
        ge=0,
        description="Detections whose text did not match any known plate format.",
    )
    unreadable_count: int = Field(
        default=0,
        ge=0,
        description="Plates that were located by the detector but could not be read by OCR.",
    )
    average_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Mean detection confidence across all records, or null if none.",
    )
    average_ocr_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Mean OCR confidence across records that produced text, or null if none.",
    )
    average_processing_time: float | None = Field(
        default=None,
        ge=0.0,
        description="Mean seconds spent per detected plate, or null if none.",
    )
    jobs_today: int = Field(default=0, ge=0, description="Uploads and sessions created today, UTC.")
    detections_today: int = Field(
        default=0, ge=0, description="License plates detected today, UTC."
    )
    by_input_type: list[InputTypeCountSchema] = Field(
        default_factory=list,
        description="Usage broken down by input type: image, video and webcam.",
    )
    daily_counts: list[DailyCountSchema] = Field(
        default_factory=list,
        description="Per-day activity over the requested window, oldest first.",
    )


class HealthResponse(BaseModel):
    """Service readiness, as reported by the health endpoint.

    Reports readiness rather than mere liveness: a process that is running but
    whose detector weights failed to load cannot serve a single detection
    request, and answering "ok" in that state would make the endpoint useless
    for the start-up measurement NFR-P4 defines.
    """

    # ``model_loaded`` collides with Pydantic's reserved ``model_`` prefix. The
    # name is the clearest one available and the guard is disabled rather than
    # the field renamed to something evasive.
    model_config = ConfigDict(protected_namespaces=())

    status: Literal["ok", "degraded"] = Field(
        ...,
        description=(
            "Overall service state. 'degraded' means the API is answering but "
            "a dependency, such as the detector weights, is unavailable."
        ),
    )
    app_name: str = Field(..., description="Name of the service.")
    version: str = Field(..., description="Running backend version.")
    database_connected: bool = Field(
        ..., description="Whether the database responded to a test query."
    )
    model_loaded: bool = Field(
        ..., description="Whether the detection model weights are loaded and ready."
    )
    uptime_seconds: float = Field(
        ..., ge=0.0, description="Seconds elapsed since the service started."
    )
    timestamp: dt.datetime = Field(
        ..., description="UTC timestamp at which this response was generated."
    )


class ErrorResponse(BaseModel):
    """The body returned for every failed request.

    Deliberately minimal. It carries no stack trace, no exception class name,
    no filesystem path and no SQL -- that material is written to the log
    instead, keyed by the same ``request_id`` that appears here (NFR-S4).

    ``request_id`` is what connects the two halves: a user quoting the
    identifier from an error screen lets a developer retrieve the exact
    traceback behind it, without the traceback ever having been sent to the
    user.

    ``message`` is Vietnamese, because it is displayed verbatim in the
    interface. Clients should branch on ``error``, which is stable, rather than
    on the message text, which may be reworded.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "FILE_TOO_LARGE",
                "message": (
                    "Tệp tải lên có dung lượng 24.3 MB, vượt quá giới hạn 10 MB. "
                    "Vui lòng chọn tệp nhỏ hơn."
                ),
                "request_id": "8c1d4f9a2b7e4c5d9f0a1b2c3d4e5f60",
            }
        }
    )

    error: str = Field(
        ...,
        description=(
            "Stable machine-readable error code, e.g. VALIDATION_ERROR or "
            "FILE_TOO_LARGE. Clients should branch on this rather than on the "
            "message text."
        ),
        examples=["FILE_TOO_LARGE"],
    )
    message: str = Field(
        ...,
        description=(
            "User-facing message in Vietnamese, safe to display directly. "
            "Never contains technical details or stack traces."
        ),
    )
    request_id: str | None = Field(
        default=None,
        description=(
            "Correlation identifier for this request. Quote it in a bug report "
            "to let a developer locate the matching server-side log entry."
        ),
        examples=["8c1d4f9a2b7e4c5d9f0a1b2c3d4e5f60"],
    )
