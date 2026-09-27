"""
error_handlers.py — graceful failure handling.

Domain errors are translated into precise HTTP status codes instead of
ugly 500s — a professional API contract:

    FileValidationError -> 415 Unsupported Media Type
    ProfileError        -> 400 Bad Request (invalid profile values)
    StorageError        -> 503 Service Unavailable (storage outage)
    DietEngineError     -> 503 Service Unavailable (plan generation failed)
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.utils.validators import FileSizeError, FileValidationError
from backend.ai_engine.diet_engine import DietEngineError
from backend.cloud.storage_service import StorageError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(FileSizeError)
    async def _file_size_handler(_: Request, exc: FileSizeError):
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(FileValidationError)
    async def _file_validation_handler(_: Request, exc: FileValidationError):
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(StorageError)
    async def _storage_handler(_: Request, exc: StorageError):
        # Cloud object storage is temporarily unavailable — client may retry.
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": f"Storage service unavailable: {exc}"},
        )

    @app.exception_handler(DietEngineError)
    async def _diet_engine_handler(_: Request, exc: DietEngineError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": f"Diet engine unavailable: {exc}"},
        )

    @app.exception_handler(ValueError)
    async def _value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
