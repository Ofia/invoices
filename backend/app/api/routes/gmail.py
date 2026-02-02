"""
Gmail API Routes

Handles Gmail integration for automatic invoice detection and download.

Endpoints:
- POST /gmail/sync - Sync Gmail inbox and download invoice PDFs

Workflow:
1. User authenticates with Gmail scope (done during OAuth)
2. User clicks "Sync Gmail" button in workspace
3. Backend searches Gmail for emails with PDF attachments
4. Filters by supplier email or invoice keywords in subject
5. Downloads PDF attachments to storage
6. Creates pending_documents for user review
7. Tracks processed email IDs to prevent duplicates
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.services.gmail_service import sync_gmail_invoices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gmail", tags=["Gmail Integration"])


class GmailSyncRequest(BaseModel):
    """Request body for Gmail sync"""
    workspace_id: int


class GmailSyncResponse(BaseModel):
    """Response after Gmail sync"""
    message: str
    emails_scanned: int
    invoices_detected: int
    documents_created: int
    duplicates_skipped: int


@router.post("/sync", response_model=GmailSyncResponse)
async def sync_gmail(
    workspace_id: int = Query(..., description="Workspace ID to sync emails to"),
    days_back: int = Query(7, ge=1, le=90, description="Number of days back to search (1-90, default: 7)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync Gmail inbox and automatically detect invoice emails.

    This endpoint:
    1. Uses stored OAuth refresh token to access Gmail
    2. Searches for emails with PDF attachments
    3. Filters by:
       - Sender matches known supplier email OR
       - Subject contains keywords: "invoice", "bill", "payment", etc.
    4. Downloads PDF attachments
    5. Creates pending documents for user review
    6. Prevents duplicate processing using gmail_message_id

    Query Parameters:
        workspace_id: ID of workspace to add detected invoices to (required)
        days_back: Number of days to look back (1-90, default: 7)
                  Maximum: 90 days (3 months)
                  Examples:
                  - 7: Last week (default, recommended for first sync)
                  - 30: Last month
                  - 90: Last 3 months (maximum allowed)

    Returns:
        Sync statistics:
        - emails_scanned: Total emails checked
        - invoices_detected: Emails with PDF attachments that matched criteria
        - documents_created: New pending documents created
        - duplicates_skipped: Emails already processed before

    Raises:
        404: Workspace not found or not owned by user
        400: User not authenticated with Gmail scope
        500: Gmail API error or sync failed

    Example:
        POST /gmail/sync?workspace_id=1&days_back=30

        Response:
        {
            "message": "Gmail sync completed successfully",
            "emails_scanned": 25,
            "invoices_detected": 5,
            "documents_created": 3,
            "duplicates_skipped": 2
        }

    Notes:
        - First-time users need to re-authenticate to grant Gmail scope
        - Default is last 7 days (safe starting point)
        - Maximum date range: 90 days (3 months)
        - Maximum 100 emails per sync (Gmail API limit)
        - All documents require manual user approval before becoming invoices
        - Recommendation: Start with 7 days, increase gradually if needed
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

    # Check if user has refresh token (Gmail scope authorized)
    if not current_user.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Gmail access not authorized. Please re-authenticate with Gmail permissions. "
                "Log out and log in again to grant Gmail access."
            )
        )

    # Perform Gmail sync
    try:
        logger.info(
            f"User {current_user.id} initiated Gmail sync for workspace {workspace_id} "
            f"(last {days_back} days)"
        )

        stats = await sync_gmail_invoices(
            db=db,
            user=current_user,
            workspace_id=workspace_id,
            days_back=days_back
        )

        return GmailSyncResponse(
            message="Gmail sync completed successfully",
            emails_scanned=stats["emails_scanned"],
            invoices_detected=stats["invoices_detected"],
            documents_created=stats["documents_created"],
            duplicates_skipped=stats["duplicates_skipped"]
        )

    except Exception as e:
        logger.error(f"Gmail sync failed for user {current_user.id}: {str(e)}")

        # Provide helpful error messages
        error_message = str(e)

        if "refresh" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail authorization expired. Please re-authenticate by logging out and logging in again."
            )
        elif "quota" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gmail API quota exceeded. Please try again later."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gmail sync failed: {error_message}"
            )


@router.get("/status")
async def check_gmail_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check if user has Gmail access authorized.

    Returns:
        {
            "gmail_authorized": true/false,
            "message": "Status message"
        }

    Example:
        GET /gmail/status

        Response (authorized):
        {
            "gmail_authorized": true,
            "message": "Gmail access is authorized"
        }

        Response (not authorized):
        {
            "gmail_authorized": false,
            "message": "Gmail access not authorized. Please re-authenticate."
        }
    """
    has_refresh_token = bool(current_user.refresh_token)

    if has_refresh_token:
        return {
            "gmail_authorized": True,
            "message": "Gmail access is authorized"
        }
    else:
        return {
            "gmail_authorized": False,
            "message": "Gmail access not authorized. Please re-authenticate to grant Gmail permissions."
        }
