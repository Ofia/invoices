"""
Supplier API Routes

Suppliers are entities that send invoices (electricians, plumbers, etc.).
Each supplier belongs to a workspace and has a markup percentage for calculations.

Endpoints:
- GET /suppliers?workspace_id={id} - List suppliers in workspace
- GET /suppliers/{id}/invoices - Get all invoices for supplier (for download)
- POST /suppliers - Create new supplier
- PUT /suppliers/{id} - Update supplier info
- DELETE /suppliers/{id} - Delete supplier and cascade to invoices
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    InvoiceResponse
)
from app.models.user import User
from app.models.workspace import Workspace
from app.models.supplier import Supplier
from app.models.invoice import Invoice
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


class SupplierDeleteResponse(BaseModel):
    """Response model for supplier deletion"""
    message: str
    supplier_name: str
    invoices_deleted: int


@router.get("/", response_model=list[SupplierResponse])
async def list_suppliers(
    workspace_id: int = Query(..., description="Workspace ID to filter suppliers"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all suppliers in a workspace.

    Query Parameters:
        workspace_id: ID of the workspace (required)

    Returns:
        List of suppliers ordered by name

    Raises:
        404: Workspace not found or not owned by user

    Example:
        GET /suppliers?workspace_id=1
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

    # Get suppliers for this workspace
    suppliers = db.query(Supplier).filter(
        Supplier.workspace_id == workspace_id
    ).order_by(Supplier.name).all()

    return suppliers


@router.get("/{supplier_id}/invoices", response_model=list[InvoiceResponse])
async def get_supplier_invoices(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all invoices for a supplier.

    Used by frontend to allow downloading invoices before deletion.

    Args:
        supplier_id: ID of the supplier

    Returns:
        List of invoices for this supplier

    Raises:
        404: Supplier not found or not owned by user

    Example:
        GET /suppliers/5/invoices
    """
    # Fetch supplier and verify ownership via workspace
    supplier = db.query(Supplier).join(Workspace).filter(
        Supplier.id == supplier_id,
        Workspace.user_id == current_user.id
    ).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )

    # Get all invoices for this supplier
    invoices = db.query(Invoice).filter(
        Invoice.supplier_id == supplier_id
    ).order_by(Invoice.invoice_date.desc()).all()

    return invoices


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new supplier in a workspace.

    Business Logic:
    - Workspace must exist and be owned by user
    - Name is required (min 1 character)
    - Email is optional but must be valid format
    - Markup percentage must be >= 0

    Args:
        supplier_data: Supplier creation data

    Returns:
        Created supplier object

    Raises:
        404: Workspace not found or not owned by user
        422: Validation error (invalid email, negative markup, etc.)

    Example Request:
        POST /suppliers
        {
            "name": "ABC Electric",
            "email": "billing@abcelectric.com",
            "markup_percentage": 15.5,
            "workspace_id": 1
        }
    """
    # Verify workspace exists and user owns it
    workspace = db.query(Workspace).filter(
        Workspace.id == supplier_data.workspace_id,
        Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Create supplier
    supplier = Supplier(
        name=supplier_data.name.strip(),
        email=supplier_data.email,
        markup_percentage=supplier_data.markup_percentage,
        workspace_id=supplier_data.workspace_id
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    logger.info(
        f"User {current_user.id} created supplier {supplier.id} "
        f"({supplier.name}) in workspace {workspace.id}"
    )

    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update supplier information.

    Business Logic:
    - Only workspace owner can update
    - All fields are optional (only updates provided fields)
    - Name must be min 1 character if provided
    - Markup percentage must be >= 0 if provided

    Args:
        supplier_id: ID of supplier to update
        supplier_data: Updated supplier data

    Returns:
        Updated supplier object

    Raises:
        404: Supplier not found or not owned by user
        422: Validation error

    Example Request:
        PUT /suppliers/5
        {
            "name": "ABC Electric Co.",
            "markup_percentage": 18.0
        }
    """
    # Fetch supplier and verify ownership via workspace
    supplier = db.query(Supplier).join(Workspace).filter(
        Supplier.id == supplier_id,
        Workspace.user_id == current_user.id
    ).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )

    # Update only provided fields
    if supplier_data.name is not None:
        supplier.name = supplier_data.name.strip()

    if supplier_data.email is not None:
        supplier.email = supplier_data.email

    if supplier_data.markup_percentage is not None:
        supplier.markup_percentage = supplier_data.markup_percentage

    db.commit()
    db.refresh(supplier)

    logger.info(f"User {current_user.id} updated supplier {supplier.id}")

    return supplier


@router.delete("/{supplier_id}", response_model=SupplierDeleteResponse)
async def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a supplier and all associated invoices.

    Business Logic:
    - Only workspace owner can delete
    - CASCADE deletes all invoices for this supplier
    - Returns count of deleted invoices for confirmation

    Frontend Flow (to be implemented):
    1. User clicks "Delete" on supplier
    2. Frontend calls GET /suppliers/{id}/invoices to show list
    3. Frontend shows modal: "Download invoices?" + warning
    4. Warning shows: "This will delete [Name] and X invoices"
    5. User confirms → Frontend calls this DELETE endpoint

    Args:
        supplier_id: ID of supplier to delete

    Returns:
        Deletion confirmation with counts

    Raises:
        404: Supplier not found or not owned by user

    Example Response:
        {
            "message": "Supplier deleted successfully",
            "supplier_name": "ABC Electric",
            "invoices_deleted": 12
        }
    """
    # Fetch supplier and verify ownership via workspace
    supplier = db.query(Supplier).join(Workspace).filter(
        Supplier.id == supplier_id,
        Workspace.user_id == current_user.id
    ).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )

    # Count invoices that will be deleted
    invoice_count = db.query(func.count(Invoice.id)).filter(
        Invoice.supplier_id == supplier_id
    ).scalar()

    supplier_name = supplier.name

    # Delete supplier (CASCADE will delete invoices automatically)
    db.delete(supplier)
    db.commit()

    logger.info(
        f"User {current_user.id} deleted supplier {supplier_id} "
        f"({supplier_name}) with {invoice_count} invoices"
    )

    return SupplierDeleteResponse(
        message="Supplier deleted successfully",
        supplier_name=supplier_name,
        invoices_deleted=invoice_count
    )
