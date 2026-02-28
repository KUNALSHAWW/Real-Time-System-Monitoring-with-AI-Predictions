---
title: System Monitor Dashboard
emoji: 📊
colorFrom: blue
colorTo: cyan
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
license: mit
---

# Real-Time System Monitoring Dashboard

This is the Streamlit frontend for Real-Time System Monitoring with AI Predictions, designed to run on Hugging Face Spaces.

## 🚀 Features

- **Real-Time Metrics**: Live CPU, Memory, Disk, and Network monitoring
- **AI-Powered Analysis**: GROQ-powered intelligent insights
- **Predictive Forecasts**: Moving Average forecasting with anomaly risk
- **Incident Management**: Auto-generated incidents for threshold breaches
- **Email Reports**: Send HTML reports with current status
- **Host Information**: See actual container/server details

## 🔧 Configuration

### Required Environment Variable (Secret)

Set the following secret in your Hugging Face Space settings:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `BACKEND_URL` | URL of your deployed backend Space | `https://username-backend-api.hf.space` |

### How to Add Secrets in Hugging Face Spaces:

1. Go to your Space's **Settings** tab
2. Scroll to **Repository secrets**
3. Click **New secret**
4. Add `BACKEND_URL` with your backend Space URL (no trailing slash)

## 📁 Required Files

Ensure these files are in your Space:

```
├── app.py              # Main Streamlit application
├── metrics_fetcher.py  # Backend API communication
├── requirements.txt    # Python dependencies
└── README.md          # This file (with YAML metadata)
```

## 🔗 Backend Connection

This frontend connects to a FastAPI backend that provides:
- `/api/metrics/current` - Real-time system metrics
- `/api/ai/analyze` - AI-powered analysis
- `/api/predictions/forecast/{metric}` - Forecasts
- `/api/incidents/list` - Incident management
- `/api/reports/send-report` - Email reports

## 🖥️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set backend URL
export BACKEND_URL=http://localhost:8000

# Run Streamlit
streamlit run app.py
```

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Real-time metrics with gauge charts |
| **Predictions** | AI forecasts and anomaly risk |
| **Incidents** | Auto-generated & manual incidents |
| **AI Analysis** | Query your system with AI |
| **Reports** | Send email status reports |

## ⚠️ Connection Error

If you see "Cannot connect to backend":
1. Ensure your backend Space is running
2. Verify `BACKEND_URL` is set correctly
3. Check if backend Space needs to wake up (free tier sleeps)

## 📝 License

MIT License
