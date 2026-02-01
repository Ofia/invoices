"""
Documents API Routes

Handles pending documents (PDFs, images, docs) that need user review before becoming invoices.

Supported formats: PDF, PNG, JPG, JPEG, WEBP, DOC, DOCX
Max file size: 10MB

Workflow:
1. Document uploaded manually or synced from Gmail
2. Goes to pending_documents table with status="pending"
3. User reviews in queue (can preview document)
4. User chooses: "Process" (convert to invoice) or "Reject" (delete)

Endpoints:
- POST /documents/upload - Upload document manually
- GET /documents?workspace_id={id} - List pending documents
- POST /documents/{id}/process - Process document (AI extraction, create invoice)
- POST /documents/{id}/reject - Reject and delete document
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_user
from app.api.schemas import PendingDocumentResponse
from app.models.user import User
from app.models.workspace import Workspace
from app.models.pending_document import PendingDocument
from app.models.supplier import Supplier
from app.models.invoice import Invoice
from app.utils.storage import save_document_file, delete_document_file, get_document_full_path
from app.utils.document_parser import extract_text_from_document
from app.services.ai_extraction import extract_invoice_data, validate_extracted_data
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentProcessRequest(BaseModel):
    """Request body for processing a document (future: add AI options)"""
    pass


class DocumentProcessResponse(BaseModel):
    """Response after processing a document"""
    message: str
    invoice_id: int


@router.post("/upload", response_model=PendingDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: int = Form(..., description="Workspace ID for this document"),
    file: UploadFile = File(..., description="Document file to upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document manually.

    This endpoint accepts multipart/form-data with a document file.
    The document enters the pending queue for user review.

    Supported formats: PDF, PNG, JPG, JPEG, WEBP, DOC, DOCX
    Max file size: 10MB

    Form Parameters:
        workspace_id: ID of workspace to add document to
        file: Document file (PDF, image, or doc)

    Returns:
        Created pending document object

    Raises:
        404: Workspace not found or not owned by user
        400: Invalid file type or file too large

    Example (using curl):
        curl -X POST http://localhost:8000/documents/upload \\
          -H "Authorization: Bearer {token}" \\
          -F "workspace_id=1" \\
          -F "file=@/path/to/invoice.pdf"
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

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed: {allowed}"
        )

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()  # Get position (file size)
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {max_mb}MB"
        )

    # Save file to storage
    try:
        file_path = await save_document_file(
            file_content=file.file,
            workspace_id=workspace_id,
            original_filename=file.filename
        )
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )

    # Create pending document record
    document = PendingDocument(
        workspace_id=workspace_id,
        filename=file.filename,
        pdf_url=file_path,  # Still called pdf_url in DB but stores any file type
        status="pending"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    logger.info(
        f"User {current_user.id} uploaded document {document.id} "
        f"({file.filename}) to workspace {workspace_id}"
    )

    return document


@router.get("/", response_model=list[PendingDocumentResponse])
async def list_documents(
    workspace_id: int = Query(..., description="Workspace ID to filter documents"),
    status_filter: str = Query(
        "pending",
        description="Filter by status (pending, processed, rejected)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List pending documents in a workspace.

    Query Parameters:
        workspace_id: ID of the workspace (required)
        status_filter: Filter by document status (default: pending)

    Returns:
        List of documents ordered by upload date (newest first)

    Raises:
        404: Workspace not found or not owned by user

    Example:
        GET /documents?workspace_id=1&status_filter=pending
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

    # Get documents for this workspace
    documents = db.query(PendingDocument).filter(
        PendingDocument.workspace_id == workspace_id,
        PendingDocument.status == status_filter
    ).order_by(PendingDocument.uploaded_at.desc()).all()

    return documents


@router.post("/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(
    document_id: int,
    process_data: DocumentProcessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process a pending document into an invoice using AI extraction.

    Business Logic:
    1. Extract text from document (PDF/image)
    2. Send to Claude AI for data extraction
    3. Match supplier by email
    4. Calculate markup_total = original_total * (1 + markup_percentage)
    5. Create Invoice record
    6. Update document status to "processed"

    Args:
        document_id: ID of document to process

    Returns:
        Process confirmation with invoice ID

    Raises:
        404: Document not found or not owned by user
        400: Document already processed, rejected, or processing failed
        500: Text extraction or AI processing failed

    Example:
        POST /documents/5/process
        {}
    """
    # Fetch document and verify ownership via workspace
    document = db.query(PendingDocument).join(Workspace).filter(
        PendingDocument.id == document_id,
        Workspace.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check if already processed
    if document.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document already {document.status.value}"
        )

    # Step 1: Extract text from document
    try:
        file_path = get_document_full_path(document.pdf_url)
        logger.info(f"Extracting text from: {file_path}")

        document_text = extract_text_from_document(file_path)

        if not document_text or len(document_text.strip()) < 10:
            raise Exception("Insufficient text extracted from document")

        logger.info(f"Extracted {len(document_text)} characters from document")

    except Exception as e:
        logger.error(f"Text extraction failed for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from document: {str(e)}"
        )

    # Step 2: Extract invoice data using AI
    try:
        logger.info("Calling Claude AI for data extraction")
        extracted_data = await extract_invoice_data(document_text)
        logger.info(f"AI extracted data: {extracted_data}")

    except Exception as e:
        logger.error(f"AI extraction failed for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI extraction failed: {str(e)}"
        )

    # Step 3: Validate extracted data
    is_valid, error_message = validate_extracted_data(extracted_data)
    if not is_valid:
        logger.error(f"Validation failed: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid extracted data: {error_message}"
        )

    # Step 4: Match supplier by email
    supplier_email = extracted_data["supplier_email"]
    supplier = db.query(Supplier).filter(
        Supplier.workspace_id == document.workspace_id,
        Supplier.email == supplier_email
    ).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No supplier found with email: {supplier_email}. Please add supplier first."
        )

    # Step 5: Calculate markup
    original_total = float(extracted_data["total_amount"])
    markup_total = original_total * (1 + supplier.markup_percentage / 100)

    logger.info(
        f"Calculated markup: ${original_total:.2f} → ${markup_total:.2f} "
        f"({supplier.markup_percentage}% markup)"
    )

    # Step 6: Create Invoice
    invoice = Invoice(
        workspace_id=document.workspace_id,
        supplier_id=supplier.id,
        pdf_url=document.pdf_url,
        original_total=original_total,
        markup_total=markup_total,
        invoice_date=extracted_data.get("invoice_date")
    )

    db.add(invoice)

    # Step 7: Update document status
    document.status = "processed"
    document.processed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(invoice)

    logger.info(
        f"User {current_user.id} processed document {document_id} → invoice {invoice.id} "
        f"(${original_total:.2f} → ${markup_total:.2f})"
    )

    return DocumentProcessResponse(
        message="Document processed successfully",
        invoice_id=invoice.id
    )


@router.post("/{document_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a pending document.

    Marks document as rejected and deletes the PDF file from storage.

    Args:
        document_id: ID of document to reject

    Returns:
        204 No Content on success

    Raises:
        404: Document not found or not owned by user
        400: Document already processed or rejected
    """
    # Fetch document and verify ownership via workspace
    document = db.query(PendingDocument).join(Workspace).filter(
        PendingDocument.id == document_id,
        Workspace.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check if already processed/rejected
    if document.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document already {document.status.value}"
        )

    # Delete document file from storage
    delete_success = delete_document_file(document.pdf_url)
    if not delete_success:
        logger.warning(f"Failed to delete document file: {document.pdf_url}")

    # Update document status
    document.status = "rejected"
    document.processed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        f"User {current_user.id} rejected document {document_id} "
        f"({document.filename})"
    )

    return None
