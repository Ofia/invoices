# Quick Start Guide - Testing Phase 1

This is a condensed version of the testing process. For detailed explanations, see `TESTING_PHASE1.md`.

## Step 1: Install PostgreSQL (One-time setup)

1. Download from: https://www.postgresql.org/download/windows/
2. Run installer, set password (remember it!)
3. Use port 5432, install all components

## Step 2: Create Database

### Using pgAdmin (Easy)
1. Open pgAdmin 4
2. Right-click "Databases" → Create → Database
3. Name: `invoice_db`
4. Click Save

### Using Command Line
```bash
psql -U postgres
CREATE DATABASE invoice_db;
\q
```

## Step 3: Configure Backend

Edit `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/invoice_db
```
Replace `YOUR_PASSWORD` with your PostgreSQL password.

## Step 4: Run Migrations

```bash
cd backend
./venv/Scripts/alembic.exe upgrade head
```

You should see: `Running upgrade  -> 001, Initial migration`

## Step 5: Run Automated Tests

```bash
cd backend
./venv/Scripts/python.exe test_phase1.py
```

This will check:
- Imports work
- Database connects
- All 6 tables exist
- Table structure is correct
- Models work

**Expected output:**
```
Results: 6/6 tests passed
🎉 SUCCESS! Phase 1 is working correctly!
```

## Step 6: Start the Server

```bash
cd backend
./venv/Scripts/uvicorn.exe app.main:app --reload
```

Leave this running!

## Step 7: Test the API

Open a new terminal:

```bash
# Test health endpoint
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

Or open in browser: http://localhost:8000/docs

---

## That's It!

If all tests pass, Phase 1 is complete.

**What we tested:**
- PostgreSQL is installed and running ✓
- Database `invoice_db` exists ✓
- 6 tables created (users, workspaces, suppliers, invoices, pending_documents, processed_emails) ✓
- FastAPI can connect to database ✓
- Models and relationships work ✓

**Ready for Phase 2: Authentication**

---

## Common Issues

**"command not found"**
- Make sure you're in the `backend` directory
- Use full paths: `./venv/Scripts/python.exe`

**"password authentication failed"**
- Check password in `.env` matches PostgreSQL password

**"database does not exist"**
- Run Step 2 again to create the database

**"tables don't exist"**
- Run Step 4 again: `alembic upgrade head`

For detailed troubleshooting, see `TESTING_PHASE1.md`.
