"""
Workspace API Routes

Workspaces are containers for invoices and suppliers. Each user can have multiple
workspaces (e.g., one per property they manage).

Endpoints:
- GET /workspaces - List all workspaces for authenticated user
- POST /workspaces - Create new workspace
- PUT /workspaces/{id} - Update workspace name
- DELETE /workspaces/{id} - Delete workspace (blocked if has data)
- POST /workspaces/{id}/preview-consolidated-invoice - Preview consolidated invoice stats
- POST /workspaces/{id}/generate-consolidated-invoice - Generate consolidated invoice PDF
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    ConsolidatedInvoiceRequest, ConsolidatedInvoicePreview
)
from app.models.user import User
from app.models.workspace import Workspace
from app.models.supplier import Supplier
from app.models.invoice import Invoice
from app.services.pdf_generator import generate_consolidated_invoice_pdf, ConsolidatedInvoiceData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all workspaces for the authenticated user.

    Returns:
        List of workspaces ordered by creation date (newest first)

    Example Response:
        [
            {
                "id": 1,
                "name": "Property A",
                "user_id": 1,
                "created_at": "2026-02-01T10:00:00"
            }
        ]
    """
    workspaces = db.query(Workspace).filter(
        Workspace.user_id == current_user.id
    ).order_by(Workspace.created_at.desc()).all()

    return workspaces


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new workspace for the authenticated user.

    Business Logic:
    - Strips whitespace from name
    - If name is empty after stripping, uses "Workspace 1" as default
    - Associates workspace with current user

    Args:
        workspace_data: Workspace creation data (name)

    Returns:
        Created workspace object

    Example Request:
        POST /workspaces
        {
            "name": "Property A"
        }
    """
    # Strip whitespace and provide default name if empty
    name = workspace_data.name.strip()
    if not name:
        name = "Workspace 1"

    # Create workspace
    workspace = Workspace(
        name=name,
        user_id=current_user.id
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    logger.info(f"User {current_user.id} created workspace {workspace.id}: {workspace.name}")

    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update workspace name.

    Business Logic:
    - Only workspace owner can update
    - Strips whitespace from name
    - If name is empty after stripping, uses "Workspace 1" as default

    Args:
        workspace_id: ID of workspace to update
        workspace_data: Updated workspace data

    Returns:
        Updated workspace object

    Raises:
        404: Workspace not found or not owned by user
    """
    # Fetch workspace and verify ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Strip whitespace and provide default name if empty
    name = workspace_data.name.strip()
    if not name:
        name = "Workspace 1"

    # Update workspace
    workspace.name = name
    db.commit()
    db.refresh(workspace)

    logger.info(f"User {current_user.id} updated workspace {workspace.id} to: {workspace.name}")

    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a workspace.

    Business Logic:
    - Only workspace owner can delete
    - BLOCKS deletion if workspace has any suppliers
    - BLOCKS deletion if workspace has any invoices
    - User must clean up all data before deletion

    Args:
        workspace_id: ID of workspace to delete

    Returns:
        204 No Content on success

    Raises:
        404: Workspace not found or not owned by user
        400: Workspace has suppliers or invoices (cannot delete)
    """
    # Fetch workspace and verify ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Check if workspace has suppliers
    supplier_count = db.query(func.count(Supplier.id)).filter(
        Supplier.workspace_id == workspace_id
    ).scalar()

    if supplier_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete workspace with {supplier_count} supplier(s). Please delete all suppliers first."
        )

    # Check if workspace has invoices
    invoice_count = db.query(func.count(Invoice.id)).filter(
        Invoice.workspace_id == workspace_id
    ).scalar()

    if invoice_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete workspace with {invoice_count} invoice(s). Please delete all invoices first."
        )

    # Safe to delete - no data in workspace
    db.delete(workspace)
    db.commit()

    logger.info(f"User {current_user.id} deleted workspace {workspace_id}")

    return None


@router.post("/{workspace_id}/preview-consolidated-invoice", response_model=ConsolidatedInvoicePreview)
async def preview_consolidated_invoice(
    workspace_id: int,
    request_data: ConsolidatedInvoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview consolidated invoice statistics for a date range.

    Shows a summary of what will be included in the consolidated invoice
    without generating the PDF. Useful for frontend to display before user
    confirms the generation.

    Args:
        workspace_id: ID of the workspace
        request_data: Date range (start_date, end_date)

    Returns:
        ConsolidatedInvoicePreview with invoice count and totals

    Raises:
        404: Workspace not found or not owned by user
        400: Invalid date range (end_date before start_date)

    Example Request:
        POST /workspaces/1/preview-consolidated-invoice
        {
            "start_date": "2026-01-01",
            "end_date": "2026-01-31"
        }

    Example Response:
        {
            "invoice_count": 5,
            "total_original": 1000.00,
            "total_markup": 150.00,
            "total_billed": 1150.00,
            "start_date": "2026-01-01",
            "end_date": "2026-01-31"
        }
    """
    # Validate workspace ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Validate date range
    if request_data.end_date < request_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

    # Fetch invoices in date range
    invoices = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.invoice_date >= request_data.start_date,
        Invoice.invoice_date <= request_data.end_date
    ).all()

    # Calculate totals
    invoice_count = len(invoices)
    total_original = sum(inv.original_total for inv in invoices)
    total_billed = sum(inv.markup_total for inv in invoices)
    total_markup = total_billed - total_original

    logger.info(
        f"User {current_user.id} previewed consolidated invoice for workspace {workspace_id}: "
        f"{invoice_count} invoices, ${total_billed:.2f} total"
    )

    return ConsolidatedInvoicePreview(
        invoice_count=invoice_count,
        total_original=total_original,
        total_markup=total_markup,
        total_billed=total_billed,
        start_date=request_data.start_date,
        end_date=request_data.end_date
    )


@router.post("/{workspace_id}/generate-consolidated-invoice")
async def generate_consolidated_invoice(
    workspace_id: int,
    request_data: ConsolidatedInvoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and download a consolidated invoice PDF.

    Creates a professional PDF invoice for property owners showing all
    services (invoices) provided during the specified period with final
    amounts to be paid (including markup).

    Args:
        workspace_id: ID of the workspace (property)
        request_data: Date range (start_date, end_date)

    Returns:
        PDF file download (application/pdf)

    Raises:
        404: Workspace not found or not owned by user
        400: Invalid date range or no invoices found in period

    Example Request:
        POST /workspaces/1/generate-consolidated-invoice
        {
            "start_date": "2026-01-01",
            "end_date": "2026-01-31"
        }

    Returns:
        PDF file with name: "consolidated_invoice_WORKSPACE_YYYYMMDD-YYYYMMDD.pdf"
    """
    # Validate workspace ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Validate date range
    if request_data.end_date < request_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

    # Fetch invoices with supplier information in date range
    invoices = db.query(Invoice).filter(
        Invoice.workspace_id == workspace_id,
        Invoice.invoice_date >= request_data.start_date,
        Invoice.invoice_date <= request_data.end_date
    ).order_by(Invoice.invoice_date.asc()).all()

    # Check if there are any invoices
    if not invoices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No invoices found in workspace for the period "
                   f"{request_data.start_date} to {request_data.end_date}"
        )

    # Prepare invoice items for PDF generation
    invoice_items = []
    for invoice in invoices:
        invoice_items.append({
            'supplier_name': invoice.supplier.name,
            'invoice_date': invoice.invoice_date,
            'amount': invoice.markup_total  # Only show final amount (with markup)
        })

    # Create consolidated invoice data
    consolidated_data = ConsolidatedInvoiceData(
        workspace_name=workspace.name,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        invoice_items=invoice_items
    )

    # Generate PDF
    pdf_buffer = generate_consolidated_invoice_pdf(consolidated_data)

    # Generate filename
    filename = (
        f"consolidated_invoice_{workspace.name.replace(' ', '_')}_"
        f"{request_data.start_date.strftime('%Y%m%d')}-"
        f"{request_data.end_date.strftime('%Y%m%d')}.pdf"
    )

    logger.info(
        f"User {current_user.id} generated consolidated invoice for workspace {workspace_id}: "
        f"{len(invoices)} invoices, total ${consolidated_data.calculate_total():.2f}"
    )

    # Return PDF as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
