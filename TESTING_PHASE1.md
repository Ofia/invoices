# Phase 1 Testing Guide

## What We're Testing

Phase 1 created the **database foundation** for the app. We need to verify:
- PostgreSQL is installed and running
- We can create a database
- Our table definitions work correctly
- The FastAPI backend can connect to the database

## Prerequisites

You'll need to install PostgreSQL on your Windows machine.

---

## Step 1: Install PostgreSQL

### Option A: Using the Official Installer (Recommended)

1. **Download PostgreSQL:**
   - Go to: https://www.postgresql.org/download/windows/
   - Click "Download the installer"
   - Download PostgreSQL 16 or 15 (latest stable version)

2. **Run the Installer:**
   - Double-click the downloaded `.exe` file
   - Click "Next" through the setup wizard
   - **Important settings:**
     - Installation Directory: Leave default (`C:\Program Files\PostgreSQL\16`)
     - Components: Check all (PostgreSQL Server, pgAdmin 4, Command Line Tools)
     - Data Directory: Leave default
     - **Password:** Choose a password for the `postgres` user (e.g., `password123`)
       - **Write this down! You'll need it later.**
     - Port: Leave as `5432`
     - Locale: Leave default

3. **Finish Installation:**
   - Click "Next" then "Finish"
   - Uncheck "Launch Stack Builder" (not needed)

### Option B: Using Chocolatey (if you have it)

```bash
choco install postgresql
```

---

## Step 2: Verify PostgreSQL is Running

### Using Windows Services

1. Press `Win + R`
2. Type `services.msc` and press Enter
3. Look for `postgresql-x64-16` (or similar)
4. Status should say "Running"
5. If not running, right-click → "Start"

### Using Command Line

Open Git Bash and run:

```bash
# Check if PostgreSQL is running
psql --version
```

You should see something like: `psql (PostgreSQL) 16.x`

---

## Step 3: Create the Database

We need to create a database called `invoice_db` for our app.

### Using pgAdmin (Graphical Interface)

1. **Open pgAdmin 4:**
   - Search for "pgAdmin 4" in Windows Start Menu
   - Enter your master password (same as postgres user password)

2. **Connect to PostgreSQL:**
   - Expand "Servers" in the left panel
   - Right-click "PostgreSQL 16" → "Connect Server"
   - Enter the password you set during installation

3. **Create Database:**
   - Right-click "Databases" → "Create" → "Database"
   - Database name: `invoice_db`
   - Owner: `postgres`
   - Click "Save"

### Using Command Line (Alternative)

Open Git Bash and run:

```bash
# Connect to PostgreSQL (will prompt for password)
psql -U postgres

# You should see a prompt like: postgres=#

# Create the database
CREATE DATABASE invoice_db;

# Verify it was created
\l

# Exit
\q
```

---

## Step 4: Configure the Backend

Update the `.env` file with your PostgreSQL credentials:

```bash
cd backend
```

Edit `.env` file and update this line:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/invoice_db
```

Replace `YOUR_PASSWORD` with the password you set during PostgreSQL installation.

Example:
```env
DATABASE_URL=postgresql+psycopg://postgres:password123@localhost:5432/invoice_db
```

---

## Step 5: Run Database Migrations

Migrations create all the tables in the database.

```bash
cd backend

# Run migrations to create tables
./venv/Scripts/alembic.exe upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial migration
```

If you see errors, see the Troubleshooting section below.

---

## Step 6: Verify Tables Were Created

### Using pgAdmin

1. Open pgAdmin 4
2. Navigate: Servers → PostgreSQL 16 → Databases → invoice_db → Schemas → public → Tables
3. You should see 6 tables:
   - `users`
   - `workspaces`
   - `suppliers`
   - `invoices`
   - `pending_documents`
   - `processed_emails`

### Using Command Line

```bash
# Connect to the database
psql -U postgres -d invoice_db

# List all tables
\dt

# You should see output like:
#              List of relations
#  Schema |       Name        | Type  |  Owner
# --------+-------------------+-------+----------
#  public | users             | table | postgres
#  public | workspaces        | table | postgres
#  public | suppliers         | table | postgres
#  public | invoices          | table | postgres
#  public | pending_documents | table | postgres
#  public | processed_emails  | table | postgres

# View the structure of a table
\d users

# Exit
\q
```

---

## Step 7: Start the Backend Server

```bash
cd backend

# Start the FastAPI server
./venv/Scripts/uvicorn.exe app.main:app --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['C:\\Users\\ofir\\Desktop\\Projects\\Invoice Adjuster\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Leave this terminal open!** The server is now running.

---

## Step 8: Test the API Endpoints

Open a **new** Git Bash terminal (keep the server running in the other one).

### Test 1: Root Endpoint

```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Invoice Management API",
  "version": "1.0.0",
  "environment": "development"
}
```

### Test 2: Health Check (Most Important!)

```bash
curl http://localhost:8000/health
```

**Expected Response (Success):**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**If you see this, Phase 1 is working perfectly! ✓**

### Test 3: Interactive API Docs

Open your browser and go to:
- http://localhost:8000/docs

You should see the **Swagger UI** with:
- `GET /` - Root endpoint
- `GET /health` - Health check

Click "Try it out" on `/health` and click "Execute" to test it in the browser.

---

## Step 9: Inspect the Database (Optional but Educational)

Let's verify our tables are structured correctly:

```bash
# Connect to the database
psql -U postgres -d invoice_db

# View the users table structure
\d users

# View the suppliers table structure
\d suppliers

# View relationships (foreign keys)
\d invoices

# Exit
\q
```

**What you're seeing:**
- Column names and data types
- Primary keys (id columns)
- Foreign keys (relationships between tables)
- Indexes (for faster lookups)

---

## Troubleshooting

### Error: "psql: command not found"

PostgreSQL command-line tools aren't in your PATH.

**Fix:**
Add PostgreSQL to your PATH:
1. Find the PostgreSQL bin directory: `C:\Program Files\PostgreSQL\16\bin`
2. Add to Windows PATH environment variable
3. Restart Git Bash

**Alternative:** Use pgAdmin for all database operations (graphical interface).

### Error: "FATAL: password authentication failed"

Your password in `.env` doesn't match the PostgreSQL password.

**Fix:**
1. Check the password you set during installation
2. Update `DATABASE_URL` in `backend/.env`

### Error: "could not connect to server"

PostgreSQL service isn't running.

**Fix:**
1. Open `services.msc`
2. Find `postgresql-x64-16`
3. Right-click → "Start"

### Error: "No module named 'app'"

You're not in the correct directory.

**Fix:**
```bash
cd backend
./venv/Scripts/python.exe -c "import app; print('OK')"
```

### Error: "psycopg.OperationalError"

Database doesn't exist or wrong connection string.

**Fix:**
1. Verify database exists: `psql -U postgres -l`
2. Check `DATABASE_URL` in `.env`
3. Make sure you're using `postgresql+psycopg://` (not `postgresql://`)

---

## Success Checklist

Check off each item as you complete it:

- [ ] PostgreSQL installed and running
- [ ] Database `invoice_db` created
- [ ] Migrations ran successfully (`alembic upgrade head`)
- [ ] 6 tables visible in pgAdmin or `\dt`
- [ ] Backend server starts without errors
- [ ] `curl http://localhost:8000/health` returns `"database": "connected"`
- [ ] Interactive docs load at http://localhost:8000/docs

**If all items are checked, Phase 1 is complete and tested!**

---

## Understanding What We Built

### Database Tables Explained

1. **users** - Stores user accounts (email, Google login info)
2. **workspaces** - Each user can have multiple workspaces (like different businesses)
3. **suppliers** - Companies that send you invoices (with markup percentages)
4. **invoices** - The actual invoice records with totals
5. **pending_documents** - PDFs waiting for you to review and approve
6. **processed_emails** - Tracks which Gmail messages we've already processed

### Relationships

- **User → Workspaces** (1-to-many): One user can have multiple workspaces
- **Workspace → Suppliers** (1-to-many): Each workspace has its own suppliers
- **Supplier → Invoices** (1-to-many): Each supplier can have many invoices
- **Workspace → Invoices** (1-to-many): Each workspace has all its invoices

### Why Migrations?

Migrations are like version control for your database structure. Instead of manually creating tables, we write Python code that:
1. Defines what tables and columns we want
2. Can be applied to any PostgreSQL database
3. Can be rolled back if something goes wrong
4. Keeps track of what changes were made and when

---

## Next Steps

Once all tests pass, you're ready for **Phase 2: Authentication**.

This will add:
- Google OAuth login
- JWT tokens for security
- Protected API endpoints
- User session management
