"""
Invoice API Routes

Handles invoices that have been processed from pending documents.
Invoices are the final records showing original amounts and calculated markups.

Endpoints:
- GET /invoices?workspace_id={id}&sort_order=asc - List invoices with sorting
- GET /invoices/{id} - Get single invoice details
- GET /invoices/{id}/download - Download invoice file
- DELETE /invoices/{id} - Delete invoice and file
"""

import logging
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.schemas import InvoiceResponse, InvoiceWithSupplier
from app.models.user import User
from app.models.workspace import Workspace
from app.models.invoice import Invoice
from app.utils.storage import delete_document_file, get_document_full_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["Invoices"])


class SortOrder(str, Enum):
    """Sort order for invoice listing"""
    ASC = "asc"   # Oldest first (A-Z)
    DESC = "desc"  # Newest first (Z-A)


@router.get("/", response_model=list[InvoiceWithSupplier])
async def list_invoices(
    workspace_id: int = Query(..., description="Workspace ID to filter invoices"),
    sort_order: SortOrder = Query(
        SortOrder.ASC,
        description="Sort by invoice date: 'asc' (oldest first) or 'desc' (newest first)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all invoices in a workspace.

    Query Parameters:
        workspace_id: ID of the workspace (required)
        sort_order: Sort by invoice date - 'asc' (oldest first, default) or 'desc' (newest first)

    Returns:
        List of invoices with supplier information, sorted by invoice date

    Raises:
        404: Workspace not found or not owned by user

    Example:
        GET /invoices?workspace_id=1&sort_order=asc
        Returns oldest invoices first (matches dashboard A-Z view)
    """
    # Verify workspace exists and user owns it
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Build query with supplier join
    query = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id
    )

    # Apply sorting
    if sort_order == SortOrder.ASC:
        query = query.order_by(Invoice.invoice_date.asc())
    else:
        query = query.order_by(Invoice.invoice_date.desc())

    invoices = query.all()

    # Convert to response model with supplier info
    # The InvoiceWithSupplier schema will automatically include supplier via relationship
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceWithSupplier)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get single invoice details with supplier information.

    Args:
        invoice_id: ID of the invoice

    Returns:
        Invoice object with supplier details

    Raises:
        404: Invoice not found or not owned by user

    Example Response:
        {
            "id": 1,
            "supplier_id": 5,
            "workspace_id": 1,
            "original_total": 100.0,
            "markup_total": 115.0,
            "invoice_date": "2025-12-10",
            "pdf_url": "uploads/documents/1/uuid_invoice.pdf",
            "created_at": "2026-02-01T10:00:00",
            "supplier": {
                "id": 5,
                "name": "ABC Electric",
                "email": "billing@abc.com",
                "markup_percentage": 15.0,
                ...
            }
        }
    """
    # Fetch invoice and verify ownership via workspace
    invoice = db.query(Invoice).join(Workspace).filter(
        Invoice.id == invoice_id,
        Workspace.user_id == current_user.id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice


@router.get("/{invoice_id}/download")
async def download_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download invoice file (PDF, image, or document).

    Serves the original file that was uploaded/processed.

    Args:
        invoice_id: ID of the invoice

    Returns:
        File download response with appropriate headers

    Raises:
        404: Invoice not found, not owned by user, or file not found

    Example:
        GET /invoices/5/download
        Returns the file with proper content-type and download headers
    """
    # Fetch invoice and verify ownership via workspace
    invoice = db.query(Invoice).join(Workspace).filter(
        Invoice.id == invoice_id,
        Workspace.user_id == current_user.id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Get full file path
    file_path = get_document_full_path(invoice.pdf_url)

    # Check if file exists
    if not file_path.exists():
        logger.error(f"Invoice {invoice_id} file not found: {invoice.pdf_url}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice file not found on server"
        )

    # Determine media type based on extension
    ext = file_path.suffix.lower()
    media_type_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    # Return file for download
    # filename parameter sets the download filename in browser
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=f"invoice_{invoice_id}{ext}"
    )


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an invoice and its associated file.

    Permanently removes the invoice record and deletes the file from storage.

    Args:
        invoice_id: ID of the invoice to delete

    Returns:
        204 No Content on success

    Raises:
        404: Invoice not found or not owned by user

    Example:
        DELETE /invoices/5
    """
    # Fetch invoice and verify ownership via workspace
    invoice = db.query(Invoice).join(Workspace).filter(
        Invoice.id == invoice_id,
        Workspace.user_id == current_user.id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Delete file from storage
    delete_success = delete_document_file(invoice.pdf_url)
    if not delete_success:
        logger.warning(f"Failed to delete invoice file: {invoice.pdf_url}")

    # Delete invoice record
    db.delete(invoice)
    db.commit()

    logger.info(
        f"User {current_user.id} deleted invoice {invoice_id} "
        f"(original: ${invoice.original_total}, markup: ${invoice.markup_total})"
    )

    return None
