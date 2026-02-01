"""
File Storage Utilities

Handles document file storage operations (PDFs, images, docs).
Currently uses local filesystem, designed to be easily swapped
for S3/cloud storage in production.

Storage Structure:
    uploads/
    └── documents/
        └── {workspace_id}/
            └── {unique_filename}.{ext}
"""

import os
import uuid
from pathlib import Path
from typing import BinaryIO
from app.core.config import settings


def get_upload_dir() -> Path:
    """
    Get the base upload directory path.

    Returns:
        Path object for upload directory
    """
    # Upload dir relative to backend folder
    upload_path = Path(__file__).parent.parent.parent / settings.UPLOAD_DIR
    return upload_path


def ensure_workspace_dir(workspace_id: int) -> Path:
    """
    Ensure workspace-specific documents directory exists.

    Creates: uploads/documents/{workspace_id}/

    Args:
        workspace_id: Workspace ID for organization

    Returns:
        Path to workspace documents directory
    """
    workspace_dir = get_upload_dir() / "documents" / str(workspace_id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename to avoid collisions.

    Format: {uuid}_{original_name}.{ext}
    Example: a1b2c3d4-5678-90ab-cdef-1234567890ab_invoice.pdf

    Args:
        original_filename: Original uploaded filename

    Returns:
        Unique filename string
    """
    # Extract extension (.pdf, .png, .jpg, etc.)
    ext = Path(original_filename).suffix.lower()
    # Generate UUID prefix
    unique_id = str(uuid.uuid4())
    # Sanitize original filename (remove path separators)
    safe_name = Path(original_filename).name

    return f"{unique_id}_{safe_name}"


async def save_document_file(
    file_content: BinaryIO,
    workspace_id: int,
    original_filename: str
) -> str:
    """
    Save uploaded document file to local storage.

    Supports PDFs, images, and document formats.

    Args:
        file_content: File binary content
        workspace_id: Workspace ID for organization
        original_filename: Original filename from upload

    Returns:
        Relative path to saved file (e.g., "uploads/documents/1/uuid_invoice.pdf")

    Raises:
        IOError: If file save fails
    """
    # Ensure directory exists
    workspace_dir = ensure_workspace_dir(workspace_id)

    # Generate unique filename
    unique_filename = generate_unique_filename(original_filename)

    # Full file path
    file_path = workspace_dir / unique_filename

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(file_content.read())

    # Return relative path (for database storage)
    relative_path = f"uploads/documents/{workspace_id}/{unique_filename}"
    return relative_path


def delete_document_file(file_path: str) -> bool:
    """
    Delete document file from storage.

    Args:
        file_path: Relative path to document file

    Returns:
        True if deleted, False if file not found
    """
    # Construct full path
    full_path = Path(__file__).parent.parent.parent / file_path

    try:
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_document_full_path(file_path: str) -> Path:
    """
    Convert relative document path to full filesystem path.

    Args:
        file_path: Relative path from database

    Returns:
        Full Path object to document file
    """
    return Path(__file__).parent.parent.parent / file_path
