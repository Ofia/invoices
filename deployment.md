# Invoice Adjuster — Full Deployment Guide

**Last updated:** 2026-02-22
**Status of progress so far:**
- ✅ AWS S3 bucket + IAM user created
- ✅ Supabase project + database created
- ✅ Render account + GitHub repo connected
- ✅ Code changes done (storage.py, documents.py, render.yaml)
- ⏳ Render deploy failing — need logs (see Step 4)
- ⏳ Vercel — attempted but 404 error (see Step 5 for detailed redo)
- ⏳ Database migrations not yet run
- ⏳ Google OAuth production URLs not yet added

---

## Overview of Services

| What | Service | Status |
|------|---------|--------|
| Frontend (React app) | Vercel | ⏳ Needs redo (see Step 5) |
| Backend (FastAPI) | Render.com | ⏳ Deploy failing (need logs) |
| Database (PostgreSQL) | Supabase | ✅ Created |
| File Storage (PDFs) | AWS S3 | ✅ Created |

---

## STEP 1 — AWS S3 ✅ DONE

**Saved credentials:** *(kept out of git — stored in your local notes / password manager)*
```
AWS_ACCESS_KEY_ID     = [see your downloaded .csv from IAM]
AWS_SECRET_ACCESS_KEY = [see your downloaded .csv from IAM]
AWS_BUCKET_NAME       = invoice-invoice-adjuster-uploads-ofia
AWS_REGION            = eu-north-1
```

> ⚠️ Note: Your region is `eu-north-1` (Stockholm) — several places below that previously said `eu-central-1` have been corrected.

---

## STEP 2 — Supabase ✅ DONE

**Saved connection string:**
```
postgresql://postgres:?#27+da8Z.UzWe!@db.dobiyxzhjajbduvfcfmh.supabase.co:5432/postgres
```

> ⚠️ **CRITICAL — URL-encode the password before using it in Render**
>
> Your password `?#27+da8Z.UzWe!` contains special characters that break URLs.
> You **must** use the URL-encoded version for `DATABASE_URL`:
> ```
> postgresql://postgres:[URL-ENCODED-PASSWORD]@db.dobiyxzhjajbduvfcfmh.supabase.co:5432/postgres
> ```
> (Characters encoded: `?`→`%3F`, `#`→`%23`, `+`→`%2B`, `!`→`%21`)
>
> This is almost certainly why the Render deploy is failing — the database URL is being parsed incorrectly.

---

## STEP 3 — Code Changes ✅ DONE (by Claude Code)

Three files were updated:

1. **`backend/render.yaml`** ← NEW — Render service configuration
2. **`backend/app/utils/storage.py`** ← UPDATED — S3 upload/delete/presigned URL support
3. **`backend/app/api/routes/documents.py`** ← UPDATED — downloads S3 files to temp storage for text extraction

**What changed in storage.py:**
- `save_document_file()`: if `STORAGE_TYPE=s3`, uploads to S3, returns the S3 key (`documents/{workspace_id}/uuid_file.pdf`)
- `delete_document_file()`: if S3, deletes from S3 bucket
- `get_s3_presigned_url()`: generates temporary signed URL for viewing files
- `get_document_for_processing()`: context manager — downloads file from S3 to temp location for AI extraction, then cleans it up

**Commit and push these changes to GitHub** (Render auto-deploys from your repo).

---

## STEP 4 — Render Backend Deployment ⏳ IN PROGRESS

### 4.1 — Fix Environment Variables (URGENT — do this before retrying deploy)

Your Render service needs these exact values. Several were wrong in the previous attempt:

Go to your Render service → **Environment** tab → update these:

```
DATABASE_URL          = postgresql://postgres:[URL-ENCODED-PASSWORD]@db.dobiyxzhjajbduvfcfmh.supabase.co:5432/postgres
GOOGLE_CLIENT_ID      = [from your local .env]
GOOGLE_CLIENT_SECRET  = [from your local .env]
GOOGLE_REDIRECT_URI   = https://invoice-adjuster-api.onrender.com/auth/google/callback
ANTHROPIC_API_KEY     = [from your local .env]
JWT_SECRET_KEY        = [from your local .env]
STORAGE_TYPE          = s3
AWS_ACCESS_KEY_ID     = [from your IAM .csv]
AWS_SECRET_ACCESS_KEY = [from your IAM .csv]
AWS_BUCKET_NAME       = invoice-invoice-adjuster-uploads-ofia
AWS_REGION            = eu-north-1
ENVIRONMENT           = production
FRONTEND_URL          = https://[your-vercel-url].vercel.app   ← fill in after Step 5
BACKEND_URL           = https://invoice-adjuster-api.onrender.com
```

> **Most likely cause of the failed deploy:** `DATABASE_URL` had an unencoded password.
> Fix it with the encoded version above and re-deploy.

### 4.2 — Provide Render Deploy Logs

**Please paste the Render deploy logs here so Claude Code can diagnose the exact error.**

To get logs:
1. Go to your Render service
2. Click the **Logs** tab (or look at the last failed deploy)
3. Copy the error section and paste it in the chat

### 4.3 — Run Database Migrations (after deploy succeeds)

Since the Render free tier has no shell access, run migrations locally pointing at Supabase:

```bash
cd backend
DATABASE_URL="postgresql://postgres:[URL-ENCODED-PASSWORD]@db.dobiyxzhjajbduvfcfmh.supabase.co:5432/postgres" alembic upgrade head
```

> This runs the Alembic migrations on the Supabase database. Run it once from your local machine.
> You need PostgreSQL client libraries installed locally (they're in requirements.txt via psycopg).

### 4.4 — Verify Backend is Running

Visit: `https://invoice-adjuster-api.onrender.com/health`
Expected: `{"status": "healthy", "database": "connected"}`

> ⚠️ Free tier spins down after 15 minutes of inactivity — first request takes ~30s. This is normal.

---

## STEP 5 — Vercel Frontend Deployment ⏳ NEEDS REDO

Your previous deploy failed with `404: NOT_FOUND` because Vercel deployed from the repo root, not from the `frontend/` folder. Here is a more detailed walkthrough to fix it.

### 5.1 — Delete the Broken Project

1. Go to [https://vercel.com/dashboard](https://vercel.com/dashboard)
2. Click on the project that failed
3. Go to **Settings** → scroll to the very bottom → **Delete Project** → confirm

### 5.2 — Create a New Project With Correct Settings

1. Back on the dashboard, click **Add New… → Project**
2. Find your GitHub repo (`Invoice-Adjuster` or whatever it's named) → click **Import**
3. You'll land on the "Configure Project" screen. **Before clicking Deploy**, do these:

**a) Set the Root Directory:**
- Look for **"Root Directory"** — it has a small pencil/edit icon next to it
- Click that pencil icon
- A text box appears — type: `frontend`
- Click the checkmark to confirm
- The field should now show `frontend/` and a note saying "Framework Preset: Vite" should auto-appear

**b) Set the Environment Variable:**
- Scroll down to the **"Environment Variables"** section (it's on the same page, below the build settings)
- Click **Add** (or "Add Variable")
- Fill in:
  - Name: `VITE_API_URL`
  - Value: `https://invoice-adjuster-api.onrender.com`
- Click **Add** to confirm the variable

**c) Verify Build Settings (should be auto-detected):**
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

4. Click **Deploy**

### 5.3 — If It Deploys But Shows a Blank Page or 404

This can happen if the Build Command or Output Directory wasn't picked up correctly.

1. Go to your Vercel project → **Settings** → **General**
2. Scroll to **Build & Development Settings**
3. Confirm:
   - Root Directory: `frontend`
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Go to the **Deployments** tab → click the three dots on the latest deploy → **Redeploy**

### 5.4 — Note Your Vercel URL

After a successful deploy, you'll see a URL like:
`https://invoice-adjuster-abc123.vercel.app`

→ Go back to Render and update `FRONTEND_URL` with this URL
→ Then complete Step 6

---

## STEP 6 — Google OAuth: Add Production URLs

> Waiting on Vercel URL from Step 5.

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Make sure your project is selected (top-left dropdown)
3. Left sidebar: **APIs & Services** → **Credentials**
4. Click your OAuth 2.0 Client ID
5. Under **"Authorized JavaScript origins"** click **+ Add URI**:
   ```
   https://your-app.vercel.app
   ```
6. Under **"Authorized redirect URIs"** click **+ Add URI**:
   ```
   https://invoice-adjuster-api.onrender.com/auth/google/callback
   ```
7. Click **Save**

---

## STEP 7 — End-to-End Smoke Test

Run through this checklist after everything is deployed:

- [ ] Visit `https://your-app.vercel.app` → page loads
- [ ] Click "Login with Google" → OAuth flow completes → you're logged in
- [ ] Create a workspace → workspace appears
- [ ] Add a supplier → supplier saved
- [ ] Upload a PDF invoice → file appears in S3 bucket (check AWS console)
- [ ] Process the invoice → AI extracts data → invoice created
- [ ] Visit `https://invoice-adjuster-api.onrender.com/health` → `{"status":"healthy"}`
- [ ] Generate consolidated invoice PDF → downloads correctly

---

## Summary: Environment Variables Master List

### Backend (set in Render dashboard)
```env
DATABASE_URL=postgresql://postgres:[URL-ENCODED-PASSWORD]@db.dobiyxzhjajbduvfcfmh.supabase.co:5432/postgres
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_REDIRECT_URI=https://invoice-adjuster-api.onrender.com/auth/google/callback
ANTHROPIC_API_KEY=sk-ant-xxx
JWT_SECRET_KEY=your-32-char-random-string
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=[from your IAM .csv]
AWS_SECRET_ACCESS_KEY=[from your IAM .csv]
AWS_BUCKET_NAME=invoice-invoice-adjuster-uploads-ofia
AWS_REGION=eu-north-1
ENVIRONMENT=production
FRONTEND_URL=https://your-app.vercel.app
BACKEND_URL=https://invoice-adjuster-api.onrender.com
```

### Frontend (set in Vercel dashboard)
```env
VITE_API_URL=https://invoice-adjuster-api.onrender.com
```
