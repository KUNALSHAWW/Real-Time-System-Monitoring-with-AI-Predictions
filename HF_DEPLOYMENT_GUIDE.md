# 🚀 Hugging Face Spaces Deployment Guide

This guide will walk you through deploying the Real-Time System Monitoring application on Hugging Face Spaces.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Hugging Face Spaces                       │
│                                                              │
│  ┌─────────────────────┐      ┌─────────────────────────┐  │
│  │   Backend Space     │      │    Frontend Space       │  │
│  │   (Docker SDK)      │◄────►│    (Streamlit SDK)      │  │
│  │                     │      │                         │  │
│  │  - FastAPI         │      │  - Streamlit Dashboard  │  │
│  │  - psutil metrics  │      │  - Plotly charts        │  │
│  │  - GROQ AI         │      │  - Real-time updates    │  │
│  │  - Email reports   │      │                         │  │
│  └─────────────────────┘      └─────────────────────────┘  │
│         Port 7860                     Port 7860             │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Part 1: Deploy the Backend (Docker Space)

#### 1.1 Create Backend Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in:
   - **Owner**: Your username
   - **Space name**: `system-monitor-backend`
   - **License**: MIT
   - **SDK**: Select **Docker**
   - **Visibility**: Public (or Private with Pro)
4. Click **"Create Space"**

#### 1.2 Upload Backend Files

Upload these files/folders to your Space:

```
system-monitor-backend/
├── Dockerfile           # HF-optimized Dockerfile
├── main.py              # FastAPI app
├── requirements.txt     # Python dependencies
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   ├── notifications.py
│   ├── rbac.py
│   └── state_manager.py
├── middleware/
│   ├── __init__.py
│   ├── error_handler.py
│   └── logging_middleware.py
└── routers/
    ├── __init__.py
    ├── ai_analysis.py
    ├── anomaly_detection.py
    ├── authentication.py
    ├── incidents.py
    ├── predictions.py
    ├── reports.py
    ├── system_metrics.py
    └── websocket.py
```

#### 1.3 Set Backend Secrets

1. Go to your Space's **Settings** tab
2. Scroll to **Repository secrets**
3. Add these secrets:

| Secret Name | Required | Value |
|-------------|----------|-------|
| `GROQ_API_KEY` | **Yes** | Your Groq API key from [console.groq.com](https://console.groq.com) |
| `EMAIL_USER` | Optional | Your Gmail address |
| `EMAIL_PASS` | Optional | Gmail App Password (not regular password!) |

#### 1.4 Wait for Build

- The Space will automatically build (2-5 minutes)
- Check the **Logs** tab for build progress
- Once complete, you'll see "Running" status

#### 1.5 Get Backend URL

Your backend URL will be:
```
https://{username}-system-monitor-backend.hf.space
```

Test it by visiting:
```
https://{username}-system-monitor-backend.hf.space/docs
```

---

### Part 2: Deploy the Frontend (Streamlit Space)

#### 2.1 Create Frontend Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in:
   - **Owner**: Your username
   - **Space name**: `system-monitor-dashboard`
   - **License**: MIT
   - **SDK**: Select **Streamlit**
   - **Visibility**: Public
4. Click **"Create Space"**

#### 2.2 Upload Frontend Files

Upload these files:

```
system-monitor-dashboard/
├── README.md            # MUST have YAML metadata at top!
├── app.py               # Main Streamlit app
├── metrics_fetcher.py   # API communication
└── requirements.txt     # Python dependencies
```

**⚠️ IMPORTANT**: The `README.md` MUST start with YAML metadata:

```yaml
---
title: System Monitor Dashboard
emoji: 📊
colorFrom: blue
colorTo: cyan
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
---
```

#### 2.3 Set Frontend Secret

1. Go to your Space's **Settings** tab
2. Scroll to **Repository secrets**
3. Add:

| Secret Name | Value |
|-------------|-------|
| `BACKEND_URL` | `https://{username}-system-monitor-backend.hf.space` |

**Note**: Replace `{username}` with your actual Hugging Face username!

#### 2.4 Wait for Build

- The Space will automatically build (1-2 minutes)
- Check the **Logs** tab for progress
- Once complete, your dashboard is live!

---

## Post-Deployment Verification

### Test Backend

```bash
# Health check
curl https://{username}-system-monitor-backend.hf.space/health

# Get current metrics
curl https://{username}-system-monitor-backend.hf.space/api/metrics/current

# Test AI (requires GROQ_API_KEY)
curl -X POST https://{username}-system-monitor-backend.hf.space/api/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "How is my system doing?"}'
```

### Test Frontend

1. Visit: `https://{username}-system-monitor-dashboard.hf.space`
2. Verify:
   - ✅ Connection status shows "Connected to Backend"
   - ✅ CPU, Memory, Disk metrics display real values
   - ✅ Host info shows Linux container details
   - ✅ AI Analysis works (if GROQ key configured)

---

## Troubleshooting

### Backend Issues

| Problem | Solution |
|---------|----------|
| "Application error" | Check Logs tab for Python errors |
| "Building" stuck | Try restarting the Space |
| GROQ not working | Verify `GROQ_API_KEY` is set correctly |
| Port issues | Dockerfile must use port 7860 |

### Frontend Issues

| Problem | Solution |
|---------|----------|
| "Cannot connect to backend" | Check `BACKEND_URL` secret |
| Dashboard blank | Check Logs for import errors |
| No auto-refresh | Install `streamlit-autorefresh` |

### Common Fixes

1. **Space sleeping (free tier)**:
   - Free Spaces sleep after inactivity
   - Just visit the URL to wake it up
   - Takes ~30 seconds to restart

2. **CORS errors**:
   - Backend already has CORS configured for `*`
   - Should work out of the box

3. **Wrong Python version**:
   - Backend Dockerfile uses Python 3.9
   - Frontend uses HF's default Streamlit Python

---

## Environment Variables Reference

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | (required) | Groq API key |
| `GROQ_MODEL` | `llama-3.1-70b-versatile` | Groq model |
| `EMAIL_USER` | - | Gmail address |
| `EMAIL_PASS` | - | Gmail App Password |
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |

---

## Features Checklist

After deployment, verify these features work:

- [ ] Real-time CPU/Memory/Disk metrics
- [ ] Host information (hostname, OS, cores)
- [ ] Historical charts (after ~1 minute of data)
- [ ] Predictions page with forecasts
- [ ] Auto-incidents (when CPU > 90%)
- [ ] AI Analysis (requires GROQ key)
- [ ] Email reports (requires EMAIL config)

---

## Upgrading

To update your Spaces:

1. Make changes to local files
2. Go to your Space's **Files** tab
3. Upload updated files (or use Git)
4. Space will automatically rebuild

---

## Support

- **Hugging Face Docs**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Groq Console**: [console.groq.com](https://console.groq.com)
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
