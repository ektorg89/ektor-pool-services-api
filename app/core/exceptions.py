from __future__ import annotations

from typing import Any, Optional


class AppError(Exception):

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

def not_found(resource: str, resource_id: Any) -> AppError:
    return AppError(
        code=f"{resource.upper()}_NOT_FOUND",
        message=f"{resource} not found",
        status_code=404,
        details={"id": resource_id},
    )


def conflict(code: str, message: str, details: Optional[dict[str, Any]] = None) -> AppError:
    return AppError(
        code=code,
        message=message,
        status_code=409,
        details=details,
    )


def bad_request(code: str, message: str, details: Optional[dict[str, Any]] = None) -> AppError:
    return AppError(
        code=code,
        message=message,
        status_code=400,
        details=details,
    )
