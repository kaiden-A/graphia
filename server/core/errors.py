from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, status_code: int, message: str, *, details: list[Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        content: dict[str, Any] = {"error": exc.message}
        if exc.details:
            content["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"loc": list(item.get("loc", [])), "msg": item.get("msg", "Invalid value.")}
            for item in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"error": "Invalid request.", "details": details},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed."
        return JSONResponse(status_code=exc.status_code, content={"error": message})
