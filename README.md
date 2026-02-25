# Invoice Adjuster

Web app for property managers to track supplier invoices, apply markup, and generate consolidated billing PDFs for property owners.

## Stack
- **Frontend**: React + TypeScript + Vite + Shadcn/ui → deployed on Vercel
- **Backend**: Python FastAPI + PostgreSQL (Supabase) → deployed on Render.com
- **AI**: Anthropic Claude API for invoice data extraction
- **Storage**: AWS S3 (eu-north-1)
- **Auth**: Google OAuth 2.0 + Gmail API

## Local Development

```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

See `CLAUDE.md` for full project structure and `deployment.md` for deployment guide.
