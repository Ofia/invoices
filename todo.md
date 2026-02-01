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

## Phase 2: Authentication (In Progress - 95% Complete)
- [x] Implement Google OAuth flow
- [x] Create auth endpoints (/auth/google)
- [x] Set up JWT token management
- [x] Add authentication middleware
- [ ] Fix token exchange 401 error (BLOCKED - see notes below)

### Session Notes - 2026-01-31

**STATUS:** OAuth flow works but token exchange fails with 401

**What's Working:**
- ✅ Fresh Google Cloud project created ("Invoices" - ID: invoices-486021)
- ✅ OAuth client created and recognized by Google (no more "invalid_client")
- ✅ User can successfully log in with Google (consent screen works)
- ✅ OAuth callback receives authorization code
- ✅ Scopes simplified to: openid, userinfo.email, userinfo.profile (Gmail removed)
- ✅ All credentials verified and match JSON file

**Current Blocker:**
- ❌ Token exchange fails with 401 Unauthorized
- Error: "Client error '401 Unauthorized' for url 'https://oauth2.googleapis.com/token'"
- This happens when exchanging authorization code for access token
- Added debug logging but need fresh session to see Google's actual error message

**Technical Details:**
- Client ID: 101909665825-irjhj5iclqba22cr9ntqein7brlo6slv.apps.googleusercontent.com
- Redirect URI: http://localhost:8000/auth/google/callback
- Working OAuth URL (use this):
  ```
  https://accounts.google.com/o/oauth2/v2/auth?client_id=101909665825-irjhj5iclqba22cr9ntqein7brlo6slv.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fgoogle%2Fcallback&scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile&response_type=code&access_type=offline&prompt=consent
  ```
- Note: Direct URL works, http://localhost:8000/auth/google has browser caching issues

**Google Console Configuration:**
- Project: Invoices (invoices-486021)
- OAuth consent screen: Testing mode
- Test user: ofir08@gmail.com (confirmed added)
- Scopes configured: openid, .../auth/userinfo.email, .../auth/userinfo.profile
- APIs enabled: People API, Gmail API (for Phase 5)
- Credentials JSON downloaded and verified: C:\Users\ofir\Desktop\client_secret_101909665825-irjhj5iclqba22cr9ntqein7brlo6slv.apps.googleusercontent.com.json

**Code Changes Made:**
- Added debug logging in backend/app/services/auth.py (exchange_code_for_token function)
- Improved error handling to capture Google's detailed error messages
- Changed redirect to use 302 status code
- Removed Gmail scope temporarily for troubleshooting

**Tomorrow's Action Plan:**
1. **First thing:** Try OAuth flow in completely fresh browser (all caches cleared overnight)
2. **Check debug logs** to see Google's actual error message from token exchange
3. **Possible causes to investigate:**
   - Client secret format issue (though verified to match)
   - Redirect URI mismatch in token exchange (though should match)
   - Authorization code expiration (codes are single-use and expire quickly)
   - Google propagation delay (though OAuth recognition suggests it's propagated)
4. **If still failing:**
   - Try google-auth-oauthlib library directly as test
   - Compare our implementation vs. working examples
   - Check if authorization code is being corrupted/modified somehow
5. **Nuclear option:** Delete project and start completely fresh with new credentials

**Files to Review Tomorrow:**
- backend/app/services/auth.py (token exchange logic, lines 92-114)
- backend/app/api/routes/auth.py (callback handler)
- Server logs: Check for DEBUG output showing what we send vs. what Google returns

**Quick Test Command for Tomorrow:**
```bash
cd backend
./venv/Scripts/uvicorn.exe app.main:app --reload
# Then try OAuth URL in fresh Chrome incognito
```

**Remember:** We're VERY close - login works, just need to fix the token exchange!

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

**Current Phase:** Phase 2: Authentication
**Last Updated:** 2026-01-31
