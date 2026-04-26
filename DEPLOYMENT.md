# Deployment Guide — Render (Free Tier)

## Overview

We deploy the **FastAPI backend** and **Streamlit frontend** as two separate services on Render.

```
render.com
├── skill-assessment-backend  (Web Service — Python)
└── skill-assessment-frontend (Web Service — Python)
```

---

## Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit — SkillSense AI"
git remote add origin https://github.com/YOUR_USERNAME/skill-assessment-agent.git
git push -u origin main
```

---

## Step 2: render.yaml (Infrastructure as Code)

Create this file at the root of your repo:

```yaml
# render.yaml — Render deployment configuration
services:
  # ── Backend (FastAPI) ─────────────────────────────────────────────────
  - type: web
    name: skill-assessment-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false          # You'll set this manually in Render dashboard
      - key: PYTHON_VERSION
        value: "3.11.0"
    healthCheckPath: /health

  # ── Frontend (Streamlit) ──────────────────────────────────────────────
  - type: web
    name: skill-assessment-frontend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
    envVars:
      - key: BACKEND_URL
        value: https://skill-assessment-backend.onrender.com   # Update after backend deploys
      - key: PYTHON_VERSION
        value: "3.11.0"
```

---

## Step 3: Deploy on Render

### 3a. Deploy the Backend First

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name**: `skill-assessment-backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   - `ANTHROPIC_API_KEY` → your actual key
5. Click **Deploy**
6. Wait ~3 minutes. Note the URL: `https://skill-assessment-backend.onrender.com`

Verify backend is live:
```bash
curl https://skill-assessment-backend.onrender.com/health
# Expected: {"status": "ok", "api_key_set": true, "model": "claude-sonnet-4-20250514"}
```

### 3b. Deploy the Frontend

1. Go to Render → **New** → **Web Service**
2. Connect the same GitHub repo
3. Settings:
   - **Name**: `skill-assessment-frontend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
4. Under **Environment Variables**, add:
   - `BACKEND_URL` → `https://skill-assessment-backend.onrender.com`
5. Click **Deploy**

---

## Step 4: Set Environment Variables in Render Dashboard

Go to your service → **Environment** tab:

| Service | Variable | Value |
|---|---|---|
| Backend | `ANTHROPIC_API_KEY` | `sk-ant-api03-...` |
| Backend | `PYTHON_VERSION` | `3.11.0` |
| Frontend | `BACKEND_URL` | `https://skill-assessment-backend.onrender.com` |
| Frontend | `PYTHON_VERSION` | `3.11.0` |

---

## Common Deployment Errors & Fixes

### ❌ "ModuleNotFoundError: No module named 'backend'"

**Cause**: Render runs `uvicorn` from a different working directory.

**Fix**: Change start command to:
```
uvicorn backend.main:app --host 0.0.0.0 --port $PORT --app-dir .
```
Or add a `Procfile` at root:
```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### ❌ "Connection refused" from frontend to backend

**Cause**: `BACKEND_URL` is still pointing to `localhost`.

**Fix**: Set `BACKEND_URL` env var on the frontend service to the full Render URL of the backend.

### ❌ Streamlit shows blank page on Render

**Cause**: Missing `--server.headless true` flag.

**Fix**: Ensure start command includes `--server.headless true --server.address 0.0.0.0`.

### ❌ PDF upload fails with 413 error

**Cause**: Render's free tier has a 10MB request body limit.

**Fix**: Add to `main.py`:
```python
from fastapi import FastAPI
app = FastAPI()
# Increase body size limit
from starlette.middleware.base import BaseHTTPMiddleware
```
Or use Render's paid tier which has no body size limit.

### ❌ "anthropic.AuthenticationError: invalid x-api-key"

**Fix**: Double-check `ANTHROPIC_API_KEY` in Render dashboard. Make sure there are no leading/trailing spaces.

### ❌ Service spins down (free tier cold start)

**Cause**: Render free tier spins down after 15 minutes of inactivity. Cold starts take ~30 seconds.

**Fix for demo**: Hit the `/health` endpoint a minute before your demo to wake the service.
Or use a free uptime monitor like [UptimeRobot](https://uptimerobot.com) to ping it every 5 minutes.

---

## Verify Deployment

```bash
# 1. Backend health
curl https://skill-assessment-backend.onrender.com/health

# 2. Test upload
curl -X POST https://skill-assessment-backend.onrender.com/upload \
  -F "resume=@samples/sample_resume.txt" \
  -F "jd_text=$(cat samples/sample_jd.txt)"

# 3. Frontend
open https://skill-assessment-frontend.onrender.com
```

---

## Alternative: Railway Deployment

If Render gives issues, Railway is equally fast:

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

Set env vars in Railway dashboard → same variables as above.
Railway URL format: `https://YOUR-APP.railway.app`
