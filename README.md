# Invoice Management App

## Overview

Web application for managing incoming invoices with AI-powered processing. Handles invoice uploads, email integration, supplier management, and markup calculations.

## Tech Stack

### Frontend
- **React + TypeScript** - Type-safe UI development
- **Vite** - Build tool
- **Shadcn/ui** - Component library for clean, functional design

### Backend
- **Python FastAPI** - Async API framework
  - Simple file upload handling
  - Clean OAuth integration
  - Native async support for concurrent operations
- **PostgreSQL** - Relational database
- **Google OAuth** - Authentication and Gmail API access
  - Libraries: `google-auth`, `authlib`

### AI & Document Processing
- **Anthropic API** - Invoice text extraction and parsing
  - Python SDK: `anthropic`
- **pandas** - CSV/Excel parsing for bulk supplier imports
- **PyPDF2 / pdfplumber** - PDF text extraction
- **pytesseract** (optional) - OCR for scanned invoices

### Storage
- **S3 or Supabase Storage** - Invoice PDF storage

### Rationale
- Python backend chosen for familiarity and document processing libraries
- FastAPI provides clean async API with automatic documentation
- React frontend allows future React Native mobile expansion
- PostgreSQL handles relational data (workspaces, suppliers, invoices)

## Core Workflows

### Email Detection Strategy

**Gmail Search Filters:**
```python
query = '''
    has:attachment 
    filename:pdf 
    after:{last_sync_date}
    (from:known_supplier_email OR subject:invoice OR subject:bill)
'''
```

**Detection Logic:**
1. Match sender email against suppliers table
2. Check subject line for keywords: "invoice", "bill", "payment"
3. If either condition is met → download PDF to pending_documents
4. Track gmail_message_id in processed_emails (prevent duplicates)

**User Review Required:**
- All documents go to "Documents" folder with "pending" status
- User previews PDF and manually approves/rejects
- Only approved documents are processed into invoices

### 1. Supplier Management

**Manual Entry:**
```
User fills form → Backend validates → Insert to DB
Fields: name, email, markup_percentage
```

**Bulk Import:**
```
User uploads CSV/Excel/PDF
  ↓
Backend parses file (pandas or Anthropic API)
  ↓
Frontend displays preview table
  ↓
User confirms → Bulk insert to suppliers table
```

**Database Schema:**
```
suppliers:
  - id
  - workspace_id
  - name
  - email
  - markup_percentage
```

### 2. Invoice Processing

**Manual Upload Flow:**
```
User drags PDF to upload area
  ↓
Upload to storage (S3/Supabase) → get URL
  ↓
Save to pending_documents table with status="pending"
  ↓
User sees document in "Documents" folder with "pending" badge
  ↓
User clicks → preview PDF
  ↓
User clicks "Process" → extract and process invoice
```

**Email Sync Flow (Hybrid Detection):**
```
User clicks "Sync Gmail"
  ↓
Gmail API search with filters:
  - has:attachment filename:pdf
  - after:{last_sync_date}
  - (from:known_supplier OR subject:invoice OR subject:bill)
  ↓
For each email:
  1. Check if sender matches known supplier email
  2. Check if subject contains keywords: "invoice", "bill"
  3. If either matches → download PDF attachment
  ↓
Save PDFs to storage (S3/Supabase)
  ↓
Insert to pending_documents table with status="pending"
  ↓
Mark gmail_message_id as processed (prevent duplicates)
  ↓
User sees new documents in "Documents" folder with "pending" badge
  ↓
User clicks document → preview PDF
  ↓
User clicks "Process" → extract invoice data and add to workspace
```

**Process Invoice (triggered by user approval):**
```
Extract text with PyPDF2/pdfplumber
  ↓
Parse for: supplier name/email, total, date
  (optional: use Anthropic API if needed)
  ↓
Match supplier by email/name in suppliers table
  ↓
Calculate markup: total * (1 + markup_percentage/100)
  ↓
Insert to invoices table
  ↓
Update pending_documents status to "processed"
  ↓
Display in dashboard
```

**Database Schema:**
```
invoices:
  - id
  - supplier_id
  - workspace_id
  - original_total
  - markup_total
  - pdf_url
  - invoice_date
  - created_at
```

**Dashboard Display:**
```
Table rows:
Supplier | Invoice Total | Total + Markup | Date

Workspace summary:
Total invoices | Total original | Total with markup
```

## API Structure

### Key Endpoints
```
POST   /auth/google                  - OAuth login
GET    /workspaces                   - List user workspaces
POST   /workspaces                   - Create workspace
POST   /suppliers                    - Add single supplier
POST   /suppliers/bulk               - Import from CSV/Excel/PDF
GET    /suppliers/{workspace}        - List suppliers
POST   /documents/upload             - Upload PDF to pending
GET    /documents/{workspace}        - List pending/processed documents
POST   /documents/{id}/process       - Process pending document to invoice
POST   /documents/{id}/reject        - Reject pending document
GET    /invoices/{workspace}         - List invoices with totals
POST   /gmail/sync                   - Sync Gmail, download PDFs to pending
```

## Database Tables

```sql
workspaces:
  - id, user_id, name, created_at

suppliers:
  - id, workspace_id, name, email, markup_percentage

invoices:
  - id, supplier_id, workspace_id, original_total, 
    markup_total, pdf_url, invoice_date, created_at

pending_documents:
  - id, workspace_id, pdf_url, filename, status,
    gmail_message_id (nullable), uploaded_at

processed_emails:
  - gmail_message_id (unique), workspace_id, processed_at

users:
  - id, email, google_id, oauth_token
```

**Document Status Flow:**
- `pending` - awaiting user review
- `processed` - approved and added to invoices
- `rejected` - user dismissed (optional)

## Development Approach

1. Build functional backend API first (FastAPI + PostgreSQL)
2. Implement authentication and Gmail OAuth
3. Build React frontend with Shadcn/ui components
4. Iterate on design in code
5. Add mobile (React Native) only if needed later

## Notes

- Mobile support deferred to post-launch
- AI used only for invoice parsing and supplier detection
- Focus on clean, functional interface over visual complexity

