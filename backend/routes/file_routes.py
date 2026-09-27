"""
file_routes.py — CLOUD OBJECT STORAGE endpoints.

POST   /api/files/upload            upload a meal image / food log (validated)
GET    /api/files                   list MY file metadata
GET    /api/files/{id}/download     download MY file's bytes (authorized)
DELETE /api/files/{id}              delete MY file (storage + metadata row)

Design points demonstrated:
  * metadata in the cloud DATABASE, bytes in OBJECT STORAGE
  * three-layer upload validation (extension, size, magic bytes)
  * USER ISOLATION: downloads/deletes check the metadata row's owner
  * transactional-ish cleanup: if the DB row fails after upload, we
    delete the orphaned object (see docs/failure-handling.md)
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.cloud.storage_service import (
    StorageError,
    build_storage_path,
    get_storage_provider,
)
from backend.config import settings
from backend.database import get_db
from backend.models import User, UserFile
from backend.schemas.schemas import FileOut
from backend.utils.security import CurrentUser
from backend.utils.validators import is_safe_storage_path, validate_file

logger = logging.getLogger("diet.files")
router = APIRouter(prefix="/api/files", tags=["files"])

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp", "pdf", "txt", "csv"]


@router.post("/upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...),
    current: CurrentUser = None,
    db: Session = Depends(get_db),
):
    """Validate + store an uploaded file in object storage, save metadata."""
    data = file.file.read()
    try:
        ext = validate_file(
            filename=file.filename or "unnamed",
            data=data,
            allowed_extensions=ALLOWED_EXTENSIONS,
            max_size_mb=settings.MAX_FILE_SIZE_MB,
        )
    finally:
        file.file.close()

    storage_path = build_storage_path(current.id, file.filename or f"upload.{ext}")

    # ---- 1. bytes -> object storage ----
    provider = get_storage_provider()
    provider.upload(data, storage_path)

    # ---- 2. metadata -> cloud database (rollback storage on failure) ----
    try:
        meta = UserFile(
            user_id=current.id,
            filename=file.filename or f"upload.{ext}",
            storage_path=storage_path,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(data),
        )
        db.add(meta)
        db.commit()
        db.refresh(meta)
    except Exception:
        provider.delete(storage_path)  # don't leave orphaned objects behind
        raise

    logger.info("User %s uploaded %s (%d bytes) -> %s",
                current.id, meta.filename, len(data), storage_path)
    return meta


@router.get("", response_model=list[FileOut])
def list_files(current: CurrentUser, db: Session = Depends(get_db)):
    """List the caller's uploaded files (metadata only), newest first."""
    return (
        db.query(UserFile)
        .filter(UserFile.user_id == current.id)
        .order_by(UserFile.uploaded_at.desc())
        .all()
    )


@router.get("/{file_id}/download")
def download_file(file_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """
    Authorized download: only the owner can fetch the bytes.

    In cloud mode the Supabase provider could hand back a 300-second
    signed URL instead of streaming bytes — both patterns are shown in
    docs/storage-design.md.
    """
    meta = (
        db.query(UserFile)
        .filter(UserFile.id == file_id, UserFile.user_id == current.id)
        .first()
    )
    if meta is None or not is_safe_storage_path(meta.storage_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")

    try:
        data = get_storage_provider().download(meta.storage_path)
    except StorageError as exc:
        logger.error("Download failed for %s: %s", meta.storage_path, exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Storage unavailable") from exc

    return Response(
        content=data,
        media_type=meta.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{meta.filename}"'},
    )


@router.delete("/{file_id}")
def delete_file(file_id: str, current: CurrentUser, db: Session = Depends(get_db)):
    """Delete the object from storage AND the metadata row (owner only)."""
    meta = (
        db.query(UserFile)
        .filter(UserFile.id == file_id, UserFile.user_id == current.id)
        .first()
    )
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")

    get_storage_provider().delete(meta.storage_path)  # best effort
    db.delete(meta)
    db.commit()
    logger.info("User %s deleted file %s", current.id, file_id)
    return {"detail": "File deleted", "id": file_id}
