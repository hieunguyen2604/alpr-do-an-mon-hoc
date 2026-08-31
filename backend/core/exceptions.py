"""API exception hierarchy: structured error codes, Vietnamese user-facing messages (NFR-S4)."""

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
    """Base class for every error the API deliberately returns to a client."""

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
        """Create an API error."""
        self.internal_detail = internal_detail or self.__class__.__name__
        self.user_message = user_message or self.default_user_message
        self.context: dict[str, Any] = context or {}
        # The Exception payload is the *internal* text: it is what appears in a
        # traceback, and tracebacks are server-side artefacts.
        super().__init__(self.internal_detail)

    def to_response_dict(self, request_id: str | None = None) -> dict[str, Any]:
        """Build the response body for this error."""
        body: dict[str, Any] = {
            "error": self.error_code,
            "message": self.user_message,
        }
        if request_id is not None:
            body["request_id"] = request_id
        return body

    def log_fields(self) -> dict[str, Any]:
        """Return the structured fields to attach to the log record."""
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
    """Raised when the request itself is malformed or self-contradictory."""

    status_code = _HTTP_BAD_REQUEST
    error_code = "VALIDATION_ERROR"
    default_user_message = (
        "Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại thông tin và thử lại."
    )


class NotFoundError(APIError):
    """Raised when a requested record does not exist."""

    status_code = _HTTP_NOT_FOUND
    error_code = "NOT_FOUND"
    default_user_message = "Không tìm thấy dữ liệu bạn yêu cầu."

    @classmethod
    def for_resource(cls, resource: str, identifier: object) -> NotFoundError:
        """Build a not-found error naming the resource in the internal detail."""
        return cls(
            f"{resource} with id={identifier!r} was not found",
            context={"resource": resource, "resource_id": str(identifier)},
        )


class FileTooLargeError(APIError):
    """Raised when an upload exceeds the configured size ceiling (NFR-S3)."""

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
        """Build the error with both sizes stated in the Vietnamese message."""
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
    """Raised when an upload's media type is not accepted (NFR-S1)."""

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
        """Build the error recording what was detected and what was allowed."""
        return cls(
            f"Rejected media type {detected_type!r}; allowed: {allowed_types}",
            context={
                "detected_type": detected_type,
                "allowed_types": allowed_types,
                "original_filename": filename,
            },
        )


class ProcessingError(APIError):
    """Raised when the request was valid but the server failed to complete it."""

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
        """Wrap an ``ai`` package exception as an API-level processing error."""
        return cls(
            f"{stage} stage failed: {type(error).__name__}: {error}",
            context={"stage": stage, "error_type": type(error).__name__, **(context or {})},
        )
