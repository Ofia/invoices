# Backend Setup Guide

## Prerequisites

1. Python 3.11+
2. PostgreSQL 14+
3. Virtual environment activated

## Installation Steps

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

Create a new PostgreSQL database:

```sql
CREATE DATABASE invoice_db;
CREATE USER invoice_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE invoice_db TO invoice_user;
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

Update the following in `.env`:
- `DATABASE_URL` - Your PostgreSQL connection string
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- `ANTHROPIC_API_KEY` - From Anthropic
- `JWT_SECRET_KEY` - Generate a secure random string
- `AWS_*` credentials if using S3 storage

### 4. Run Database Migrations

```bash
# Run migrations to create tables
alembic upgrade head
```

### 5. Start the Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Verify Installation

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Database Commands

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current migration version
alembic current

# View migration history
alembic history
```

## Troubleshooting

### Database Connection Issues

If you get connection errors, verify:
1. PostgreSQL is running
2. Database exists
3. Credentials in `.env` are correct
4. Use `postgresql+psycopg://` prefix (not `postgresql://`)

### Import Errors

Make sure you're in the `backend` directory and the virtual environment is activated:

```bash
cd backend
source venv/Scripts/activate  # Windows Git Bash
# or
source venv/bin/activate      # Linux/Mac
```
