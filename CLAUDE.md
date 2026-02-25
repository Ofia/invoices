# Invoice Adjuster — Claude Reference

## Purpose
Web app for property managers to track supplier invoices, apply markup, and generate consolidated billing PDFs for property owners.

## Tech Stack
- **Frontend**: React 19 + TypeScript + Vite + Shadcn/ui + Tailwind v4 — `frontend/`
- **Backend**: Python FastAPI + SQLAlchemy + Alembic — `backend/`
- **Auth**: Google OAuth 2.0 + JWT + Gmail API
- **AI**: Anthropic Claude API (`claude-sonnet-4-5`) — invoice data extraction
- **Storage**: AWS S3 (`eu-north-1`, bucket: `invoice-invoice-adjuster-uploads-ofia`)
- **DB**: PostgreSQL via Supabase

## Key Backend Files
```
backend/app/
  main.py                      # FastAPI entry, CORS reads FRONTEND_URL from env
  core/config.py               # All settings (pydantic-settings, reads .env)
  core/database.py             # SQLAlchemy session
  api/routes/
    auth.py                    # Google OAuth flow
    documents.py               # Upload, process, reject documents
    invoices.py                # Invoice list, download, consolidated PDF
    suppliers.py               # Supplier CRUD
    workspaces.py              # Workspace CRUD
    gmail.py                   # Gmail sync
    search.py                  # Global search
  api/schemas.py               # Pydantic request/response schemas
  models/                      # SQLAlchemy models (user, workspace, supplier, invoice, pending_document, processed_email)
  services/
    ai_extraction.py           # Claude API call, JSON parsing, retry on 529
    gmail_service.py           # Gmail API integration
    pdf_generator.py           # ReportLab consolidated invoice PDF
  utils/
    storage.py                 # S3 + local file storage (STORAGE_TYPE env var)
    document_parser.py         # PDF/image text extraction (pdfplumber)
    jwt.py                     # JWT encode/decode
```

## Key Frontend Files
```
frontend/src/
  App.tsx                      # Router setup, protected routes
  contexts/
    AuthContext.tsx             # JWT token management
    WorkspaceContext.tsx        # Active workspace state
  lib/api/
    client.ts                  # Axios instance with auth interceptor
    index.ts                   # All API call functions
    types.ts                   # TypeScript types
  pages/
    dashboard/DashboardPage.tsx
    documents/DocumentsPage.tsx   # Upload, process, reject, Gmail sync
    invoices/InvoicesPage.tsx     # Invoice table, consolidated PDF generation
    suppliers/SuppliersPage.tsx
    auth/LoginPage.tsx
```

## Database Models
- `users` — id, email, google_id, oauth_token, refresh_token
- `workspaces` — id, user_id, name
- `suppliers` — id, workspace_id, name, email, markup_percentage
- `invoices` — id, workspace_id, supplier_id, original_total, markup_total, pdf_url, invoice_date
- `pending_documents` — id, workspace_id, filename, pdf_url, status (pending/processed/rejected), gmail_message_id
- `processed_emails` — gmail_message_id, workspace_id (dedup table)

## Document Processing Flow
1. PDF uploaded → S3 (`documents/{workspace_id}/{uuid_filename}`)
2. Text extracted (pdfplumber)
3. Claude AI extracts: `supplier_email`, `invoice_date`, `total_amount`
4. Supplier matched by email in workspace
5. `markup_total = original_total * (1 + markup_percentage / 100)`
6. Invoice record created, document marked processed

## Deployment
- **Frontend**: Vercel (auto-deploy from GitHub `master`)
- **Backend**: Render.com (auto-deploy from GitHub, `backend/` root, `render.yaml` present)
- **DB**: Supabase PostgreSQL — run migrations: `DATABASE_URL=<url> alembic upgrade head`
- **Storage**: AWS S3, region `eu-north-1`

## Required Env Vars (backend)
```
DATABASE_URL          # Supabase postgres URL (URL-encode special chars in password)
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI
ANTHROPIC_API_KEY
JWT_SECRET_KEY
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_BUCKET_NAME
AWS_REGION=eu-north-1
FRONTEND_URL          # Vercel URL (for CORS)
```
