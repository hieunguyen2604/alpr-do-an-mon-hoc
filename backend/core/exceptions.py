"""The API exception hierarchy and its user-facing Vietnamese messages.

This module is where NFR-S4 -- *"errors returned to the user must not leak a
stack trace"* -- stops being a guideline and becomes a mechanism. Every error
carries **two** descriptions of what went wrong, and they are never the same
audience:

============================ ==================================================
Field                        Audience and destination
============================ ==================================================
:attr:`APIError.user_message`  The end user. Vietnamese, plain, actionable.
                               Goes into the HTTP response body.
:attr:`APIError.internal_detail` The developer. English, technical, may name
                               files, sizes and library errors. Goes into the
                               log **only**.
============================ ==================================================

Keeping them as separate attributes rather than as a convention removes the
usual failure mode, where a technical string reaches the user because the
person writing the ``raise`` had only one message field available and used it
for the thing they most needed to see.

Hierarchy::

    APIError                        (base, carries status_code)
    ├── ValidationError             400  bad request payload
    ├── NotFoundError               404  record does not exist
    ├── FileTooLargeError           413  upload over the configured ceiling
    ├── UnsupportedMediaTypeError   415  MIME type not accepted
    └── ProcessingError             500  pipeline or storage failure

The exception handler registered on the FastAPI app catches :class:`APIError`
once, logs :attr:`~APIError.internal_detail` together with the traceback, and
returns a body built solely from :attr:`~APIError.user_message`, the error code
and the request identifier.

Why the user-facing text is Vietnamese
--------------------------------------
The project rule is that source code, comments and Swagger descriptions are
English while the interface the examiner sees is Vietnamese. The strings in
this module are interface text that happens to live in a Python file -- they
are rendered verbatim in the frontend -- so they follow the interface rule, not
the code rule.

Relationship with ``ai.inference.exceptions``
---------------------------------------------
The ``ai`` package raises its own family rooted at ``ALPRError``, with English
developer-facing messages and no notion of HTTP. The service layer is the
translation point: it catches ``ALPRError`` and re-raises the matching class
from this module, typically :class:`ProcessingError`, putting the original
message into ``internal_detail``. That is what lets the pipeline stay free of
any web framework (NFR-M1) while still producing decent HTTP responses.

.. note::
   :class:`ValidationError` shares its name with ``pydantic.ValidationError``.
   A module needing both should import one under an alias, e.g.
   ``from pydantic import ValidationError as PydanticValidationError``.
"""

from __future__ import annotations

from typing import Any, Final

__all__ = [
    "APIError",
    "ValidationError",
    "NotFoundError",
    "FileTooLargeError",
    "UnsupportedMediaTypeError",
    "ProcessingError",
]

_HTTP_BAD_REQUEST: Final[int] = 400
_HTTP_NOT_FOUND: Final[int] = 404
_HTTP_PAYLOAD_TOO_LARGE: Final[int] = 413
_HTTP_UNSUPPORTED_MEDIA_TYPE: Final[int] = 415
_HTTP_INTERNAL_SERVER_ERROR: Final[int] = 500


class APIError(Exception):
    """Base class for every error the API deliberately returns to a client.

    Subclasses fix :attr:`status_code`, :attr:`error_code` and a default
    :attr:`user_message`; a call site normally supplies only
    ``internal_detail``, because the technical cause is the part that varies
    while the message shown to the user should stay consistent.

    Attributes:
        status_code: HTTP status for the response.
        error_code: Stable machine-readable identifier, e.g. ``"FILE_TOO_LARGE"``.
            The frontend switches on this rather than on the message text, so
            wording can be improved without breaking client behaviour.
        user_message: Vietnamese text shown to the end user. Must never name a
            filesystem path, an exception class or a library.
        internal_detail: English technical description, for the log only.
            Never serialised into a response.
        context: Extra structured fields merged into the log record, for
            example ``{"job_id": ..., "size_bytes": ...}``. Never serialised
            into a response either.
    """

    status_code: int = _HTTP_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    default_user_message: str = "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau."

    def __init__(
        self,
        internal_detail: str = "",
        *,
        user_message: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Create an API error.

        Args:
            internal_detail: English technical description of what failed --
                the message a developer needs. Written to the log, never to the
                response.
            user_message: Overrides the class default when a specific situation
                deserves more precise Vietnamese wording. Leave unset to use
                the class default, which is the usual case.
            context: Structured fields to attach to the log record.
        """
        self.internal_detail = internal_detail or self.__class__.__name__
        self.user_message = user_message or self.default_user_message
        self.context: dict[str, Any] = context or {}
        # The Exception payload is the *internal* text: it is what appears in a
        # traceback, and tracebacks are server-side artefacts.
        super().__init__(self.internal_detail)

    def to_response_dict(self, request_id: str | None = None) -> dict[str, Any]:
        """Build the response body for this error.

        This method is the single place where an error becomes bytes on the
        wire, and it is written so that adding a field to the class cannot
        accidentally expose it: the dictionary is constructed from an explicit
        list of safe keys rather than from ``self.__dict__``. Neither
        :attr:`internal_detail` nor :attr:`context` can appear here.

        Args:
            request_id: Correlation identifier for the current request, echoed
                back so a user reporting a problem can quote it and a developer
                can find the matching log line.

        Returns:
            A JSON-serialisable body carrying only user-safe values.
        """
        body: dict[str, Any] = {
            "error": self.error_code,
            "message": self.user_message,
        }
        if request_id is not None:
            body["request_id"] = request_id
        return body

    def log_fields(self) -> dict[str, Any]:
        """Return the structured fields to attach to the log record.

        Args:
            None.

        Returns:
            A mapping suitable for ``logger.error(..., extra=...)``, combining
            the error code, the HTTP status, the technical detail and any
            caller-supplied context.
        """
        return {
            "error_code": self.error_code,
            "status_code": self.status_code,
            "internal_detail": self.internal_detail,
            **self.context,
        }

    def __repr__(self) -> str:
        """Return a developer-facing representation naming the internal detail."""
        return (
            f"{self.__class__.__name__}(status_code={self.status_code}, "
            f"error_code={self.error_code!r}, "
            f"internal_detail={self.internal_detail!r})"
        )


class ValidationError(APIError):
    """Raised when the request itself is malformed or self-contradictory.

    Covers things the caller can fix by sending a different request: a missing
    upload field, a page number below one, a date range that ends before it
    starts, an ``input_type`` outside the accepted set.

    Not to be used for a file that is merely too large or of the wrong type --
    those have dedicated status codes (413 and 415) that clients can act on
    without parsing a message.
    """

    status_code = _HTTP_BAD_REQUEST
    error_code = "VALIDATION_ERROR"
    default_user_message = (
        "Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại thông tin và thử lại."
    )


class NotFoundError(APIError):
    """Raised when a requested record does not exist.

    Used for an unknown detection identifier, an unknown ``job_id``, or a
    stored file whose row still exists but whose bytes have gone missing from
    disk.

    The user-facing message deliberately does not distinguish "never existed"
    from "was deleted": the distinction is of no use to the user and telling
    the two apart lets an outsider probe which identifiers are real.
    """

    status_code = _HTTP_NOT_FOUND
    error_code = "NOT_FOUND"
    default_user_message = "Không tìm thấy dữ liệu bạn yêu cầu."

    @classmethod
    def for_resource(cls, resource: str, identifier: object) -> NotFoundError:
        """Build a not-found error naming the resource in the internal detail.

        A convenience for the repository layer, where the same three lines
        would otherwise be repeated for every lookup. The identifier goes into
        the log; the user still sees the generic message.

        Args:
            resource: Name of the resource type, e.g. ``"detection"`` or
                ``"job"``.
            identifier: The primary key that was looked up.

        Returns:
            A configured :class:`NotFoundError`.
        """
        return cls(
            f"{resource} with id={identifier!r} was not found",
            context={"resource": resource, "resource_id": str(identifier)},
        )


class FileTooLargeError(APIError):
    """Raised when an upload exceeds the configured size ceiling (NFR-S3).

    The limit is enforced server-side even though the frontend also checks it:
    the frontend check is a convenience, and anything reaching the API over
    HTTP may not have gone through it at all.

    Unlike most errors here, the user message is worth specialising per case --
    a user told only "file too large" cannot tell whether they are over by a
    kilobyte or by a factor of ten. Use :meth:`with_limit`.
    """

    status_code = _HTTP_PAYLOAD_TOO_LARGE
    error_code = "FILE_TOO_LARGE"
    default_user_message = (
        "Tệp tải lên vượt quá dung lượng cho phép. Vui lòng chọn tệp có kích thước nhỏ hơn."
    )

    @classmethod
    def with_limit(
        cls,
        *,
        actual_bytes: int,
        limit_bytes: int,
        filename: str | None = None,
    ) -> FileTooLargeError:
        """Build the error with both sizes stated in the Vietnamese message.

        Sizes are the one technical detail that is genuinely useful to a user:
        knowing the ceiling is 10 MB and the file is 24 MB tells them exactly
        what to do next. The filename stays out of the message -- it is the
        user's own string echoed back, and echoing user input into a rendered
        message is a habit worth not forming.

        Args:
            actual_bytes: Size of the rejected upload.
            limit_bytes: Configured ceiling that was exceeded.
            filename: Original filename, recorded in the log only.

        Returns:
            A configured :class:`FileTooLargeError`.
        """
        actual_mb = actual_bytes / (1024 * 1024)
        limit_mb = limit_bytes / (1024 * 1024)
        return cls(
            f"Upload rejected: {actual_bytes} bytes exceeds limit of {limit_bytes} bytes",
            user_message=(
                f"Tệp tải lên có dung lượng {actual_mb:.1f} MB, "
                f"vượt quá giới hạn {limit_mb:.0f} MB. "
                "Vui lòng chọn tệp nhỏ hơn."
            ),
            context={
                "actual_bytes": actual_bytes,
                "limit_bytes": limit_bytes,
                # Not "filename": that name is reserved by ``logging`` and
                # would make the log call itself raise. See
                # ``backend.core.logging.safe_extra``.
                "original_filename": filename,
            },
        )


class UnsupportedMediaTypeError(APIError):
    """Raised when an upload's media type is not accepted (NFR-S1).

    The type is determined from the file's **magic bytes**, never from its
    extension: an extension is chosen by whoever uploads the file and proves
    nothing. A ``.jpg`` that is really a ZIP archive is rejected here.
    """

    status_code = _HTTP_UNSUPPORTED_MEDIA_TYPE
    error_code = "UNSUPPORTED_MEDIA_TYPE"
    default_user_message = (
        "Định dạng tệp không được hỗ trợ. Vui lòng tải lên ảnh (JPG, PNG) hoặc video (MP4, AVI)."
    )

    @classmethod
    def with_detected_type(
        cls,
        *,
        detected_type: str,
        allowed_types: list[str],
        filename: str | None = None,
    ) -> UnsupportedMediaTypeError:
        """Build the error recording what was detected and what was allowed.

        Args:
            detected_type: MIME type read from the file's magic bytes.
            allowed_types: MIME types configured as acceptable.
            filename: Original filename, recorded in the log only.

        Returns:
            A configured :class:`UnsupportedMediaTypeError`.
        """
        return cls(
            f"Rejected media type {detected_type!r}; allowed: {allowed_types}",
            context={
                "detected_type": detected_type,
                "allowed_types": allowed_types,
                "original_filename": filename,
            },
        )


class ProcessingError(APIError):
    """Raised when the request was valid but the server failed to complete it.

    Two distinct causes end up here, and both are genuinely the server's fault
    rather than the caller's:

    * the recognition pipeline failed -- an ``ALPRError`` from the ``ai``
      package, translated at the service boundary;
    * a storage operation failed -- the disk is full, a path is not writable,
      a video could not be encoded.

    Finding no plate in an image is **not** this error. An image with no plate
    is a successful request with an empty result list, and must be reported as
    ``200`` with zero detections -- otherwise the statistics lose every
    negative case and the accuracy figures become meaningless.
    """

    status_code = _HTTP_INTERNAL_SERVER_ERROR
    error_code = "PROCESSING_ERROR"
    default_user_message = (
        "Hệ thống không xử lý được yêu cầu của bạn. Vui lòng thử lại sau ít phút."
    )

    @classmethod
    def from_pipeline_error(
        cls,
        error: Exception,
        *,
        stage: str,
        context: dict[str, Any] | None = None,
    ) -> ProcessingError:
        """Wrap an ``ai`` package exception as an API-level processing error.

        The translation point required by NFR-M1: ``ALPRError`` knows nothing
        about HTTP, and the API layer must not let its English developer text
        reach a user. The original message is preserved in
        :attr:`~APIError.internal_detail` so nothing is lost from the log.

        Args:
            error: The original exception raised by the pipeline.
            stage: Which stage failed, e.g. ``"detection"``, ``"recognition"``
                or ``"storage"``. Recorded to make failure patterns visible in
                aggregate.
            context: Additional structured fields for the log record.

        Returns:
            A configured :class:`ProcessingError`.
        """
        return cls(
            f"{stage} stage failed: {type(error).__name__}: {error}",
            context={"stage": stage, "error_type": type(error).__name__, **(context or {})},
        )
