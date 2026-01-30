# Invoice Management App - Development Tasks

## Project Setup ✅
- [x] Create project structure
- [x] Initialize Python venv
- [x] Install backend dependencies
- [x] Initialize React frontend with Vite
- [x] Initialize git repository
- [x] Create todo.md file

## Phase 1: Backend Foundation
- [ ] Set up FastAPI application structure
- [ ] Configure PostgreSQL database connection
- [ ] Create database models (SQLAlchemy)
  - [ ] Users table
  - [ ] Workspaces table
  - [ ] Suppliers table
  - [ ] Invoices table
  - [ ] Pending documents table
  - [ ] Processed emails table
- [ ] Set up Alembic for database migrations
- [ ] Create initial migration

## Phase 2: Authentication
- [ ] Implement Google OAuth flow
- [ ] Create auth endpoints (/auth/google)
- [ ] Set up JWT token management
- [ ] Add authentication middleware
- [ ] Test OAuth login flow

## Phase 3: Core API Endpoints
- [ ] Workspaces endpoints
  - [ ] GET /workspaces - List user workspaces
  - [ ] POST /workspaces - Create workspace
- [ ] Suppliers endpoints
  - [ ] POST /suppliers - Add single supplier
  - [ ] GET /suppliers/{workspace} - List suppliers
  - [ ] POST /suppliers/bulk - Import from CSV/Excel
- [ ] Documents endpoints
  - [ ] POST /documents/upload - Upload PDF
  - [ ] GET /documents/{workspace} - List documents
  - [ ] POST /documents/{id}/process - Process to invoice
  - [ ] POST /documents/{id}/reject - Reject document
- [ ] Invoices endpoints
  - [ ] GET /invoices/{workspace} - List invoices with totals

## Phase 4: Document Processing
- [ ] Implement PDF text extraction (PyPDF2/pdfplumber)
- [ ] Integrate Anthropic API for invoice parsing
- [ ] Create invoice data extraction logic
- [ ] Implement supplier matching algorithm
- [ ] Add markup calculation logic
- [ ] Set up S3 or Supabase Storage for PDFs

## Phase 5: Gmail Integration
- [ ] Set up Gmail API credentials
- [ ] Implement Gmail OAuth scope
- [ ] Create email sync logic
- [ ] Build email detection filters
- [ ] Implement PDF attachment download
- [ ] Add duplicate prevention logic
- [ ] Create /gmail/sync endpoint

## Phase 6: Frontend Foundation
- [ ] Set up React Router
- [ ] Configure Shadcn/ui components
- [ ] Create base layout with sidebar navigation
- [ ] Implement dark theme
- [ ] Set up API client (axios/fetch)
- [ ] Create authentication context

## Phase 7: Frontend Pages
- [ ] Dashboard page
  - [ ] "At a Glance" stats cards
  - [ ] Invoice volume graph
- [ ] Documents page
  - [ ] Document list view
  - [ ] PDF preview panel
  - [ ] Process/Reject actions
- [ ] Invoices page
  - [ ] Invoice table with filtering
  - [ ] Summary statistics
- [ ] Suppliers page
  - [ ] Supplier list/grid
  - [ ] Add supplier form
  - [ ] Bulk import interface
- [ ] Login page
  - [ ] Google OAuth button

## Phase 8: Testing & Polish
- [ ] Write backend unit tests
- [ ] Write API integration tests
- [ ] Test Gmail sync flow end-to-end
- [ ] Test invoice processing accuracy
- [ ] Add error handling and validation
- [ ] Implement loading states
- [ ] Add user feedback (toasts/notifications)

## Phase 9: Deployment Prep
- [ ] Create Docker configuration
- [ ] Set up environment variables
- [ ] Write deployment documentation
- [ ] Configure production database
- [ ] Set up CI/CD pipeline (optional)

## Future Enhancements
- [ ] Add invoice editing capability
- [ ] Implement invoice search
- [ ] Add export functionality (CSV/Excel)
- [ ] Create reporting dashboard
- [ ] Add email notifications
- [ ] Mobile app (React Native)

---

**Current Phase:** Project Setup
**Last Updated:** 2026-01-30
