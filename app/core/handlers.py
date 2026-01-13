from __future__ import annotations

import json
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.errors import ErrorResponse, RequestValidationErrorResponse


def _new_request_id() -> str:
    return str(uuid.uuid4())


def register_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = _new_request_id()

        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

        status_code = getattr(locals().get("response", None), "status_code", None)

        level = "info"
        if isinstance(status_code, int):
            if status_code >= 500:
                level = "error"
            elif status_code >= 400:
                level = "warning"

        log = {
            "level": level,
            "event": "request",
            "request_id": request.state.request_id,
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        }
        print(json.dumps(log, ensure_ascii=False))


        response.headers["X-Request-Id"] = request.state.request_id
        return response

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        payload = ErrorResponse(
            code=exc.code,
            message=exc.message,
            details={**exc.details, "request_id": request.state.request_id},
        ).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        payload = RequestValidationErrorResponse(
            details={
                "errors": exc.errors(),
                "request_id": request.state.request_id,
            }
        ).model_dump(mode="json")
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        payload = ErrorResponse(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            details={"request_id": request.state.request_id},
        ).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        payload = ErrorResponse(
            code="INTERNAL_SERVER_ERROR",
            message="Unexpected error",
            details={"request_id": request.state.request_id},
        ).model_dump(mode="json")
        return JSONResponse(status_code=500, content=payload)