"""Pydantic schemas for API requests and responses"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    google_id: str

class UserResponse(UserBase):
    id: int
    google_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Workspace Schemas
class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class WorkspaceResponse(WorkspaceBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Supplier Schemas
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    markup_percentage: float = Field(..., ge=0)

class SupplierCreate(SupplierBase):
    workspace_id: int

class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    markup_percentage: Optional[float] = Field(None, ge=0)

class SupplierResponse(SupplierBase):
    id: int
    workspace_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Invoice Schemas
class InvoiceBase(BaseModel):
    original_total: float = Field(..., gt=0)
    markup_total: float = Field(..., gt=0)
    invoice_date: Optional[date] = None

class InvoiceCreate(InvoiceBase):
    supplier_id: int
    workspace_id: int
    pdf_url: str

class InvoiceResponse(InvoiceBase):
    id: int
    supplier_id: int
    workspace_id: int
    pdf_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceWithSupplier(InvoiceResponse):
    supplier: SupplierResponse


# Pending Document Schemas
class PendingDocumentBase(BaseModel):
    filename: str

class PendingDocumentCreate(PendingDocumentBase):
    workspace_id: int
    pdf_url: str
    gmail_message_id: Optional[str] = None

class PendingDocumentResponse(PendingDocumentBase):
    id: int
    workspace_id: int
    pdf_url: str
    status: str
    gmail_message_id: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Bulk Import Schemas
class SupplierBulkImport(BaseModel):
    suppliers: list[SupplierBase]

class BulkImportResponse(BaseModel):
    success_count: int
    error_count: int
    errors: list[str] = []


# Dashboard/Statistics Schemas
class WorkspaceStats(BaseModel):
    total_invoices: int
    total_original: float
    total_with_markup: float
    pending_documents: int

class DashboardResponse(BaseModel):
    workspace: WorkspaceResponse
    stats: WorkspaceStats
    recent_invoices: list[InvoiceWithSupplier]


# Authentication Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str


# Manual Invoice Creation Schema
class ManualInvoiceCreate(BaseModel):
    supplier_id: int = Field(..., description="ID of the supplier for this invoice")
    original_total: float = Field(..., gt=0, description="Original invoice total amount")
    invoice_date: Optional[date] = Field(None, description="Invoice date (YYYY-MM-DD)")


# Error Response Schema
class ProcessingError(BaseModel):
    detail: str = Field(..., description="Human-readable error message")
    error_type: str = Field(..., description="Error type code (e.g., missing_email, missing_total)")
    missing_fields: Optional[list[str]] = Field(None, description="List of missing required fields")
    suggestion: Optional[str] = Field(None, description="Suggested action to resolve the error")
