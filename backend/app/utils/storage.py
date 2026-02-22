"""
File Storage Utilities

Handles document file storage operations (PDFs, images, docs).
Supports local filesystem (development) and AWS S3 (production).

Storage Structure:
    Local:  uploads/documents/{workspace_id}/{uuid_filename}.{ext}
    S3 key: documents/{workspace_id}/{uuid_filename}.{ext}

Controlled by STORAGE_TYPE env var: "local" or "s3"
"""

import os
import uuid
import tempfile
from pathlib import Path
from typing import BinaryIO
from contextlib import contextmanager
from app.core.config import settings


def _get_s3_client():
    import boto3
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def get_upload_dir() -> Path:
    upload_path = Path(__file__).parent.parent.parent / settings.UPLOAD_DIR
    return upload_path


def ensure_workspace_dir(workspace_id: int) -> Path:
    workspace_dir = get_upload_dir() / "documents" / str(workspace_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir


def generate_unique_filename(original_filename: str) -> str:
    ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())
    safe_name = Path(original_filename).name
    return f"{unique_id}_{safe_name}"


async def save_document_file(
    file_content: BinaryIO,
    workspace_id: int,
    original_filename: str
) -> str:
    """
    Save uploaded document file to storage.

    Returns:
        - Local:  "uploads/documents/{workspace_id}/{uuid_filename}"
        - S3:     "documents/{workspace_id}/{uuid_filename}"
    """
    unique_filename = generate_unique_filename(original_filename)

    if settings.STORAGE_TYPE == "s3":
        s3_key = f"documents/{workspace_id}/{unique_filename}"
        s3 = _get_s3_client()
        s3.upload_fileobj(file_content, settings.AWS_BUCKET_NAME, s3_key)
        return s3_key
    else:
        workspace_dir = ensure_workspace_dir(workspace_id)
        file_path = workspace_dir / unique_filename
        with open(file_path, "wb") as f:
            f.write(file_content.read())
        return f"uploads/documents/{workspace_id}/{unique_filename}"


def delete_document_file(file_path: str) -> bool:
    """
    Delete document file from storage.

    Args:
        file_path: S3 key (e.g. "documents/1/uuid_file.pdf") or local relative path
    """
    if settings.STORAGE_TYPE == "s3":
        try:
            s3 = _get_s3_client()
            s3.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=file_path)
            return True
        except Exception:
            return False
    else:
        full_path = Path(__file__).parent.parent.parent / file_path
        try:
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False


def get_s3_presigned_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """Generate a temporary pre-signed URL to serve a private S3 file."""
    s3 = _get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )


@contextmanager
def get_document_for_processing(file_path: str):
    """
    Context manager that yields a local Path suitable for text extraction.

    For S3: downloads file to a temp location, yields path, then cleans up.
    For local: yields the existing filesystem path directly.

    Usage:
        with get_document_for_processing(document.pdf_url) as path:
            text = extract_text_from_document(path)
    """
    if settings.STORAGE_TYPE == "s3":
        ext = Path(file_path).suffix
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        try:
            s3 = _get_s3_client()
            s3.download_fileobj(settings.AWS_BUCKET_NAME, file_path, tmp)
            tmp.close()
            yield Path(tmp.name)
        finally:
            try:
                Path(tmp.name).unlink(missing_ok=True)
            except Exception:
                pass
    else:
        yield Path(__file__).parent.parent.parent / file_path


def get_document_full_path(file_path: str) -> Path:
    """Local-only: convert relative path to full filesystem path."""
    return Path(__file__).parent.parent.parent / file_path
