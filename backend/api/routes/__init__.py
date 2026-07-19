"""The API's route modules, and the error documentation they share.

Splitting routes by resource keeps each module small enough to read in one
sitting, and it means two features being worked on at once rarely touch the
same file.

This module holds the OpenAPI descriptions of the error responses, because
those are identical across routes and Swagger has to be *told* about them --
FastAPI documents the success response automatically but has no way to know
that an endpoint may answer 413. Left undocumented, the generated client would
have no type for the error body and the frontend would be written against
whatever it observed by trial and error.
"""

from __future__ import annotations

from typing import Any, Final

from backend.schemas.detection import ErrorResponse

__all__ = [
    "ERROR_400",
    "ERROR_404",
    "ERROR_413",
    "ERROR_415",
    "ERROR_500",
    "errors",
]


def _error(description: str, code: str, message: str) -> dict[str, Any]:
    """Build one OpenAPI error-response entry.

    Args:
        description: Short English explanation shown in Swagger.
        code: The stable ``error`` code the body carries.
        message: The Vietnamese ``message`` a user would see, as an example.

    Returns:
        An entry suitable for a route's ``responses`` mapping.
    """
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            "application/json": {
                "example": {
                    "error": code,
                    "message": message,
                    "request_id": "8c1d4f9a2b7e4c5d9f0a1b2c3d4e5f60",
                }
            }
        },
    }


ERROR_400: Final[dict[int, dict[str, Any]]] = {
    400: _error(
        "The request was malformed or self-contradictory.",
        "VALIDATION_ERROR",
        "Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại thông tin và thử lại.",
    )
}

ERROR_404: Final[dict[int, dict[str, Any]]] = {
    404: _error(
        "The requested record does not exist.",
        "NOT_FOUND",
        "Không tìm thấy dữ liệu bạn yêu cầu.",
    )
}

ERROR_413: Final[dict[int, dict[str, Any]]] = {
    413: _error(
        "The upload exceeds the configured size limit.",
        "FILE_TOO_LARGE",
        "Tệp tải lên có dung lượng 24.3 MB, vượt quá giới hạn 10 MB. "
        "Vui lòng chọn tệp nhỏ hơn.",
    )
}

ERROR_415: Final[dict[int, dict[str, Any]]] = {
    415: _error(
        "The file's true type, read from its magic bytes, is not accepted.",
        "UNSUPPORTED_MEDIA_TYPE",
        "Định dạng tệp không được hỗ trợ. "
        "Vui lòng tải lên ảnh (JPG, PNG) hoặc video (MP4, AVI).",
    )
}

ERROR_500: Final[dict[int, dict[str, Any]]] = {
    500: _error(
        "The request was valid but the server could not complete it. "
        "The response never carries a stack trace; the technical detail is "
        "written to the server log under the same request_id (NFR-S4).",
        "PROCESSING_ERROR",
        "Hệ thống không xử lý được yêu cầu của bạn. Vui lòng thử lại sau ít phút.",
    )
}


def errors(*groups: dict[int, dict[str, Any]]) -> dict[int | str, dict[str, Any]]:
    """Merge several error-response groups into one ``responses`` mapping.

    Args:
        *groups: The groups to combine, e.g. ``errors(ERROR_400, ERROR_404)``.

    Returns:
        A single mapping to hand to a route's ``responses`` argument.
    """
    merged: dict[int | str, dict[str, Any]] = {}
    for group in groups:
        merged.update(group)
    return merged
