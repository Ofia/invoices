# Environment Setup Guide

## PostgreSQL PATH Issue (Windows)

If you get "psql: command not found", PostgreSQL's bin directory isn't in your PATH.

---

## Quick Fix (Per Session)

Every time you open Git Bash, run:

```bash
# Replace 18 with your PostgreSQL version (16, 17, or 18)
export PATH=$PATH:"/c/Program Files/PostgreSQL/18/bin"
```

**Or use the setup script:**

```bash
# From project root
source setup_env.sh
```

This automatically detects your PostgreSQL version and adds it to PATH.

---

## Permanent Fix

### Option 1: Edit ~/.bashrc (Recommended for Git Bash)

This makes the PATH change permanent for all Git Bash sessions:

```bash
# Edit your bashrc file
nano ~/.bashrc

# Add this line at the end (replace 18 with your version):
export PATH=$PATH:"/c/Program Files/PostgreSQL/18/bin"

# Save and exit (Ctrl+O, Enter, Ctrl+X)

# Reload bashrc
source ~/.bashrc

# Test it
psql --version
```

Now every new Git Bash terminal will have PostgreSQL in the PATH.

---

### Option 2: Windows System PATH

This makes PostgreSQL available to all programs:

1. **Open System Properties:**
   - Press `Win + X`
   - Select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"

2. **Edit PATH:**
   - Under "System variables", find and select "Path"
   - Click "Edit"
   - Click "New"
   - Add: `C:\Program Files\PostgreSQL\18\bin` (replace 18 with your version)
   - Click OK on all dialogs

3. **Restart Git Bash**
   - Close all Git Bash windows
   - Open a new one
   - Test: `psql --version`

---

## Finding Your PostgreSQL Version

Not sure which version you have? Check:

```bash
ls "/c/Program Files/PostgreSQL/"
```

You'll see folder names like `16`, `17`, or `18` - that's your version.

---

## Alternative: Use pgAdmin Instead

If you don't want to deal with command-line tools, use **pgAdmin 4** (graphical interface):

- It's installed with PostgreSQL
- No PATH configuration needed
- Visual interface for all database operations
- Easier for beginners

You can do everything in pgAdmin instead of using `psql` commands.

---

## Verification

After setting up PATH, verify it works:

```bash
# Should show version
psql --version

# Should connect (will prompt for password)
psql -U postgres -d invoice_db

# Exit
\q
```

If you see the version number, you're all set!
