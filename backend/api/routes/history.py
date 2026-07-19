"""History endpoints: listing, searching, detail, deletion and CSV export.

One ordering detail in this module is load-bearing and easy to undo by
accident. ``/history/export`` is declared **before** ``/history/{detection_id}``.
FastAPI matches routes in declaration order, and ``detection_id`` is typed as
``int``; with the order reversed, a request for ``/history/export`` would match
the detail route first, fail to parse ``"export"`` as an integer and return 422.
The endpoint would appear in Swagger, look correct in the source, and never
work. Keep the export route above the parameterised one.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from typing import Annotated, Literal

from fastapi import APIRouter, Path, Query, Response, status
from fastapi.responses import StreamingResponse

from backend.api.deps import DbSession, HistoryDep
from backend.api.routes import ERROR_400, ERROR_404, ERROR_500, errors
from backend.core.logging import get_logger
from backend.models.detection import utcnow
from backend.schemas.detection import DetectionHistoryResponse, HistoryListResponse
from backend.services.history_service import (
    MAX_PAGE_SIZE,
    HistoryFilter,
    HistoryService,
    SortField,
    SortOrder,
)

__all__ = ["router"]

logger = get_logger(__name__)

router = APIRouter(tags=["History"])

# -- Reusable query parameters ---------------------------------------------
#
# Declared once and shared by the list and the export endpoints, because the
# two must interpret every filter identically. A user who exports what they are
# looking at and receives something else has been handed wrong data with no
# indication that anything went wrong.

SearchQuery = Annotated[
    str | None,
    Query(
        description=(
            "Free-text search. Matches both the corrected plate number and the "
            "raw OCR string, so a record is still found when post-processing "
            "changed the text."
        ),
        examples=["51F"],
        max_length=64,
    ),
]
InputTypeQuery = Annotated[
    Literal["image", "video", "webcam"] | None,
    Query(description="Keep only records from this input type."),
]
ValidFormatQuery = Annotated[
    bool | None,
    Query(
        description=(
            "Keep only records that did (`true`) or did not (`false`) match a "
            "Vietnamese plate format. Omit for both."
        )
    ),
]
DateFromQuery = Annotated[
    dt.datetime | None,
    Query(
        description="Inclusive lower bound on `detected_time`, in UTC (ISO 8601).",
        examples=["2026-07-01T00:00:00Z"],
    ),
]
DateToQuery = Annotated[
    dt.datetime | None,
    Query(
        description="Inclusive upper bound on `detected_time`, in UTC (ISO 8601).",
        examples=["2026-07-19T23:59:59Z"],
    ),
]
MinConfidenceQuery = Annotated[
    float | None,
    Query(
        ge=0.0,
        le=1.0,
        description="Keep only records whose DETECTION confidence is at least this.",
        examples=[0.5],
    ),
]
JobIdQuery = Annotated[
    str | None,
    Query(
        description="Keep only the plates found in one upload.",
        examples=["3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840"],
    ),
]
SortByQuery = Annotated[
    SortField,
    Query(description="Column to sort by."),
]
OrderQuery = Annotated[
    SortOrder,
    Query(description="Sort direction."),
]


def _build_filter(
    search: str | None,
    input_type: str | None,
    is_valid_format: bool | None,
    date_from: dt.datetime | None,
    date_to: dt.datetime | None,
    min_confidence: float | None,
    job_id: str | None,
) -> HistoryFilter:
    """Assemble the service-layer filter from query parameters.

    Args:
        search: Free-text needle, or ``None``.
        input_type: Input type to keep, or ``None``.
        is_valid_format: Format-validity restriction, or ``None``.
        date_from: Inclusive lower time bound, or ``None``.
        date_to: Inclusive upper time bound, or ``None``.
        min_confidence: Lower bound on detection confidence, or ``None``.
        job_id: Upload to restrict to, or ``None``.

    Returns:
        The filter object the service consumes.
    """
    return HistoryFilter(
        search=search,
        input_type=input_type,
        is_valid_format=is_valid_format,
        date_from=date_from,
        date_to=date_to,
        min_confidence=min_confidence,
        job_id=job_id,
    )


@router.get(
    "/history",
    response_model=HistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List detection records with search, filtering and sorting",
    description=(
        "Returns one page of stored detections, newest first by default.\n\n"
        "Results are **always paginated** — there is no unpaginated variant. "
        "The table is specified to hold 100 000 records (NFR-SC2), and a single "
        "unbounded query over it would materialise every row into memory and "
        "into one response.\n\n"
        "`total` counts the records matching the current filters across all "
        "pages, not the number in this page, so it can drive a page counter "
        "directly.\n\n"
        "Note that one row is one **license plate**, not one upload: an image "
        "containing three plates appears as three rows sharing one "
        "`source_job_id`."
    ),
    responses={
        200: {
            "description": "A page of matching records.",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1247,
                                "plate_number": "51F-12345",
                                "raw_ocr_text": "51FI2345",
                                "confidence": 0.94,
                                "ocr_confidence": 0.87,
                                "input_type": "image",
                                "image_path": "/files/uploads/9c4f2b1e.jpg",
                                "plate_image_path": "/files/plates/3f2a1c7e-plate-0.jpg",
                                "bbox_x": 142,
                                "bbox_y": 318,
                                "bbox_w": 186,
                                "bbox_h": 64,
                                "bbox": {
                                    "x": 142,
                                    "y": 318,
                                    "width": 186,
                                    "height": 64,
                                },
                                "is_valid_format": True,
                                "plate_line_count": 1,
                                "processing_time": 0.412,
                                "detected_time": "2026-07-19T09:31:22.145Z",
                                "created_at": "2026-07-19T09:31:22.150Z",
                                "source_job_id": "3f2a1c7e-9b4d-4e21-a0f6-77c2d1e5b840",
                            }
                        ],
                        "total": 1247,
                        "page": 1,
                        "page_size": 20,
                        "total_pages": 63,
                        "has_next": True,
                        "has_previous": False,
                    }
                }
            },
        },
        **errors(ERROR_400, ERROR_500),
    },
)
def list_history(
    db: DbSession,
    history: HistoryDep,
    page: Annotated[
        int, Query(ge=1, description="Page number, starting at 1.", examples=[1])
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_PAGE_SIZE,
            description=f"Records per page, at most {MAX_PAGE_SIZE}.",
            examples=[20],
        ),
    ] = 20,
    search: SearchQuery = None,
    input_type: InputTypeQuery = None,
    is_valid_format: ValidFormatQuery = None,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    min_confidence: MinConfidenceQuery = None,
    job_id: JobIdQuery = None,
    sort_by: SortByQuery = SortField.DETECTED_TIME,
    order: OrderQuery = SortOrder.DESC,
) -> HistoryListResponse:
    """Return one page of detection records.

    Args:
        db: Session for this request.
        history: The history service.
        page: 1-based page number.
        page_size: Records per page.
        search: Free-text needle matched against both plate strings.
        input_type: Restrict to one input type.
        is_valid_format: Restrict by format validity.
        date_from: Inclusive lower bound on detection time.
        date_to: Inclusive upper bound on detection time.
        min_confidence: Lower bound on detection confidence.
        job_id: Restrict to one upload.
        sort_by: Column to order by.
        order: Sort direction.

    Returns:
        The requested page and the total number of matching records.

    Raises:
        ValidationError: If the paging or filter parameters are inconsistent.
    """
    criteria = _build_filter(
        search, input_type, is_valid_format, date_from, date_to, min_confidence, job_id
    )
    return history.list_history(
        db,
        page=page,
        page_size=page_size,
        criteria=criteria,
        sort_by=sort_by,
        order=order,
    )


# NOTE: this route MUST stay above ``/history/{detection_id}``. See the module
# docstring -- reversing them makes this endpoint permanently return 422.
@router.get(
    "/history/export",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
    summary="Export the matching detection records as CSV",
    description=(
        "Streams every record matching the given filters as a CSV file. The "
        "filters are identical to those of `GET /api/history`, so the export "
        "contains exactly what the user is looking at, unpaginated.\n\n"
        "The file is UTF-8 **with a byte-order mark**. That is required for "
        "Microsoft Excel, which does not auto-detect UTF-8 in a `.csv` and "
        "otherwise falls back to the system code page — turning every "
        "Vietnamese column header into mojibake. Column headers are in "
        "Vietnamese because the file is read by a person, not by a program.\n\n"
        "The response is streamed rather than assembled in memory: at the "
        "specified ceiling of 100 000 records the document is tens of "
        "megabytes."
    ),
    responses={
        200: {
            "description": "A CSV file, UTF-8 with BOM.",
            "content": {
                "text/csv": {
                    "schema": {"type": "string", "format": "binary"},
                    "example": (
                        "ID,Biển số,Chuỗi OCR thô,Độ tin cậy phát hiện,...\r\n"
                        "1247,51F-12345,51FI2345,0.9400,...\r\n"
                    ),
                }
            },
        },
        **errors(ERROR_400, ERROR_500),
    },
)
def export_history(
    history: HistoryDep,
    search: SearchQuery = None,
    input_type: InputTypeQuery = None,
    is_valid_format: ValidFormatQuery = None,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    min_confidence: MinConfidenceQuery = None,
    job_id: JobIdQuery = None,
    sort_by: SortByQuery = SortField.DETECTED_TIME,
    order: OrderQuery = SortOrder.DESC,
) -> StreamingResponse:
    """Stream the matching records as a CSV download.

    Note the absence of a ``db`` parameter, which is not an oversight. A
    dependency-provided session is closed when the endpoint *returns*, and a
    streaming response returns before its body has been produced -- the
    generator would then run against a closed session and fail halfway through
    the download. The stream therefore owns a session of its own and closes it
    when the last chunk has been written.

    Args:
        history: The history service.
        search: Free-text needle matched against both plate strings.
        input_type: Restrict to one input type.
        is_valid_format: Restrict by format validity.
        date_from: Inclusive lower bound on detection time.
        date_to: Inclusive upper bound on detection time.
        min_confidence: Lower bound on detection confidence.
        job_id: Restrict to one upload.
        sort_by: Column to order by.
        order: Sort direction.

    Returns:
        A streaming CSV response with a download filename.

    Raises:
        ValidationError: If the filter parameters are inconsistent. Raised
            before streaming starts, so the client still receives a clean 400
            rather than a truncated file.
    """
    criteria = _build_filter(
        search, input_type, is_valid_format, date_from, date_to, min_confidence, job_id
    )
    # Validated eagerly: once the first byte of a 200 has gone out, an error
    # can no longer be reported as a status code.
    criteria.validate()

    stamp = utcnow().strftime("%Y%m%d-%H%M%S")
    # ASCII filename on purpose -- a Content-Disposition header carrying
    # non-ASCII needs RFC 5987 encoding that not every browser handles the same
    # way, and the header is machine-facing rather than user-facing.
    filename = f"alpr-history-{stamp}.csv"

    return StreamingResponse(
        _stream_csv(history, criteria, sort_by, order),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _stream_csv(
    history: HistoryService,
    criteria: HistoryFilter,
    sort_by: SortField,
    order: SortOrder,
) -> Iterator[str]:
    """Produce the export's chunks against a session of the stream's own.

    Args:
        history: The history service.
        criteria: Conditions narrowing the export.
        sort_by: Column to order by.
        order: Sort direction.

    Yields:
        Chunks of CSV text.
    """
    from backend.models.database import SessionLocal  # local: keeps the import cycle open

    session = SessionLocal()
    try:
        yield from history.export_csv(
            session, criteria=criteria, sort_by=sort_by, order=order
        )
    finally:
        session.close()


@router.get(
    "/history/{detection_id}",
    response_model=DetectionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get one detection record",
    description=(
        "Returns a single stored detection, including its bounding box in both "
        "the flat (`bbox_x`, `bbox_y`, ...) and nested (`bbox`) forms, and URLs "
        "for the source image and the cropped plate.\n\n"
        "The paths are returned as URLs rather than as filesystem paths: the "
        "server's directory layout is not published, and the files are only "
        "reachable through the handler that validates the request (NFR-S2)."
    ),
    responses={
        200: {"description": "The requested record."},
        **errors(ERROR_404, ERROR_500),
    },
)
def get_detection(
    db: DbSession,
    history: HistoryDep,
    detection_id: Annotated[
        int,
        Path(ge=1, description="Identifier of the detection record.", examples=[1247]),
    ],
) -> DetectionHistoryResponse:
    """Return one detection record.

    Args:
        db: Session for this request.
        history: The history service.
        detection_id: Primary key of the record.

    Returns:
        The record.

    Raises:
        NotFoundError: If no such record exists.
    """
    return history.get_by_id(db, detection_id)


@router.delete(
    "/history/{detection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one detection record",
    description=(
        "Removes a detection record and the cropped plate image belonging to "
        "it.\n\n"
        "The **source image is kept** while any other record still references "
        "it. Several plates found in one photograph share that file, so "
        "deleting it with the first of them would leave the others pointing at "
        "nothing.\n\n"
        "Returns 204 with no body. Deleting a record that does not exist is a "
        "404 rather than a silent success, so a client can tell a completed "
        "delete from one that referred to the wrong identifier."
    ),
    responses={
        204: {"description": "The record was deleted."},
        **errors(ERROR_404, ERROR_500),
    },
)
def delete_detection(
    db: DbSession,
    history: HistoryDep,
    detection_id: Annotated[
        int,
        Path(ge=1, description="Identifier of the detection record.", examples=[1247]),
    ],
) -> Response:
    """Delete one detection record.

    Args:
        db: Session for this request.
        history: The history service.
        detection_id: Primary key of the record to delete.

    Returns:
        An empty 204 response.

    Raises:
        NotFoundError: If no such record exists.
    """
    history.delete(db, detection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
