"""
Global Search API Route

Provides unified search across invoices, suppliers, and documents.
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, String
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.invoice import Invoice
from app.models.supplier import Supplier
from app.models.pending_document import PendingDocument

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


# Response Models
class InvoiceSearchResult(BaseModel):
    id: int
    supplier_name: str
    supplier_id: int
    original_total: float
    markup_total: float
    invoice_date: str
    created_at: str
    match_field: str  # What field matched the query

    class Config:
        from_attributes = True


class SupplierSearchResult(BaseModel):
    id: int
    name: str
    email: str
    markup_percentage: float
    match_field: str

    class Config:
        from_attributes = True


class DocumentSearchResult(BaseModel):
    id: int
    filename: str
    status: str
    uploaded_at: str
    gmail_message_id: Optional[str]
    match_field: str

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    invoices: List[InvoiceSearchResult]
    suppliers: List[SupplierSearchResult]
    documents: List[DocumentSearchResult]
    total_results: int


@router.get("", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    workspace_id: int = Query(..., description="Workspace ID to search in"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Global search across invoices, suppliers, and documents.

    Searches:
    - Invoices: supplier name, invoice date, amounts
    - Suppliers: name, email
    - Documents: filename

    Query Parameters:
        q: Search query (min 2 characters)
        workspace_id: ID of workspace to search in

    Returns:
        Categorized search results with match highlights
    """
    search_term = f"%{q.lower()}%"

    # Search Invoices (with supplier name via join)
    invoices_query = (
        db.query(Invoice, Supplier)
        .join(Supplier, Invoice.supplier_id == Supplier.id)
        .filter(
            Invoice.workspace_id == workspace_id,
            or_(
                func.lower(Supplier.name).like(search_term),
                func.cast(Invoice.original_total, String).like(search_term),
                func.cast(Invoice.markup_total, String).like(search_term),
                func.cast(Invoice.invoice_date, String).like(search_term)
            )
        )
        .order_by(Invoice.created_at.desc())
        .limit(10)
        .all()
    )

    invoice_results = []
    for invoice, supplier in invoices_query:
        # Determine which field matched
        match_field = "supplier_name"
        if q.lower() in supplier.name.lower():
            match_field = "supplier_name"
        elif q.lower() in str(invoice.original_total):
            match_field = "amount"
        elif q.lower() in str(invoice.invoice_date):
            match_field = "date"

        invoice_results.append(
            InvoiceSearchResult(
                id=invoice.id,
                supplier_name=supplier.name,
                supplier_id=supplier.id,
                original_total=invoice.original_total,
                markup_total=invoice.markup_total,
                invoice_date=invoice.invoice_date.isoformat(),
                created_at=invoice.created_at.isoformat(),
                match_field=match_field
            )
        )

    # Search Suppliers
    suppliers_query = (
        db.query(Supplier)
        .filter(
            Supplier.workspace_id == workspace_id,
            or_(
                func.lower(Supplier.name).like(search_term),
                func.lower(Supplier.email).like(search_term)
            )
        )
        .order_by(Supplier.name)
        .limit(10)
        .all()
    )

    supplier_results = [
        SupplierSearchResult(
            id=s.id,
            name=s.name,
            email=s.email,
            markup_percentage=s.markup_percentage,
            match_field="name" if q.lower() in s.name.lower() else "email"
        )
        for s in suppliers_query
    ]

    # Search Pending Documents
    documents_query = (
        db.query(PendingDocument)
        .filter(
            PendingDocument.workspace_id == workspace_id,
            func.lower(PendingDocument.filename).like(search_term)
        )
        .order_by(PendingDocument.uploaded_at.desc())
        .limit(10)
        .all()
    )

    document_results = [
        DocumentSearchResult(
            id=d.id,
            filename=d.filename,
            status=d.status,
            uploaded_at=d.uploaded_at.isoformat(),
            gmail_message_id=d.gmail_message_id,
            match_field="filename"
        )
        for d in documents_query
    ]

    total = len(invoice_results) + len(supplier_results) + len(document_results)

    return SearchResponse(
        query=q,
        invoices=invoice_results,
        suppliers=supplier_results,
        documents=document_results,
        total_results=total
    )
