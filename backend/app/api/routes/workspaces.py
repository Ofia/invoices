"""
Workspace API Routes

Workspaces are containers for invoices and suppliers. Each user can have multiple
workspaces (e.g., one per property they manage).

Endpoints:
- GET /workspaces - List all workspaces for authenticated user
- POST /workspaces - Create new workspace
- PUT /workspaces/{id} - Update workspace name
- DELETE /workspaces/{id} - Delete workspace (blocked if has data)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.schemas import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.models.user import User
from app.models.workspace import Workspace
from app.models.supplier import Supplier
from app.models.invoice import Invoice

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
