# Invoice Management App - Development Tasks

## Development Guidelines

**Working Style:**
- **Explain Before Implementing**: Concisely explain what you're about to do before writing code
- **Educational Approach**: This is a learning process - explain the tools, frameworks, and techniques being used
- **Professional Quality**: Focus on creating a professional, working tool with proper error handling, validation, and best practices
- **Not Just MVP**: Take time to implement features correctly, not just quickly
- **Code Quality**: Include proper documentation, type hints, error handling, and follow Python/TypeScript best practices

## Project Setup ✅
- [x] Create project structure
- [x] Initialize Python venv
- [x] Install backend dependencies
- [x] Initialize React frontend with Vite
- [x] Initialize git repository
- [x] Create todo.md file

## Phase 1: Backend Foundation ✅
- [x] Set up FastAPI application structure
- [x] Configure PostgreSQL database connection
- [x] Create database models (SQLAlchemy)
  - [x] Users table
  - [x] Workspaces table
  - [x] Suppliers table
  - [x] Invoices table
  - [x] Pending documents table
  - [x] Processed emails table
- [x] Set up Alembic for database migrations
- [x] Create initial migration

## Phase 2: Authentication ✅
- [x] Implement Google OAuth flow
- [x] Create auth endpoints (/auth/google)
- [x] Set up JWT token management
- [x] Add authentication middleware
- [x] OAuth security improvements and cleanup

### Completion Notes - 2026-02-01

**STATUS:** ✅ Phase 2 Complete

**OAuth Implementation:**
- Google OAuth 2.0 flow fully functional
- Token exchange working correctly
- JWT token generation and validation operational
- Protected endpoints functioning properly

**Security & Stability Improvements:**
- Removed debug logging exposing client secrets
- Added 10-second timeout to Google OAuth requests
- Implemented proper HTTP status codes (400/502/504/500)
- Fixed deprecated datetime.utcnow() usage
- Made CORS configuration environment-aware
- Added proper logging throughout auth flow

**Testing:**
- End-to-end OAuth flow tested successfully
- User creation/authentication verified
- JWT token validation confirmed working

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

**Current Phase:** Phase 3: Core API Endpoints
**Last Updated:** 2026-02-01
