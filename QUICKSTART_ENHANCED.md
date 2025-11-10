# 🚀 Quick Start Guide - Production System

## ⚡ 60-Second Setup

### 1. Start the System

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend  
cd frontend
streamlit run app_enhanced.py
```

### 2. Access Dashboard

Open: http://localhost:8501

### 3. Configure (Sidebar)

```
📧 Email: your@email.com ✅
⏰ Interval: 10 seconds ⏱️
🔔 Channels: Email ✅ In-App ✅
```

### 4. Test

Click: `🧪 Test Notifications`

## 🔑 Secrets Configuration

Create: `frontend/.streamlit/secrets.toml`

```toml
# Gmail (Required for email alerts)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_16char_app_password"

# Slack (Optional)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

# PagerDuty (Optional)
PAGERDUTY_API_KEY = "your_key"
PAGERDUTY_SERVICE_KEY = "your_service_key"
```

## 📧 Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select: "Mail" → "Other"
3. Name it: "System Monitor"
4. Copy the 16-character password
5. Paste in `secrets.toml`

## 🧪 Test Commands

```bash
# Security audit
python scripts/security_audit.py

# Backend health
curl http://localhost:8000/health

# WebSocket test
wscat -c ws://localhost:8000/ws
```

## 📊 Features at a Glance

| Feature | Status | Access |
|---------|--------|--------|
| Real-Time Dashboard | ✅ | Main page |
| Email Alerts | ✅ | Auto-sends on anomaly |
| In-App Notifications | ✅ | Sidebar 🔔 |
| WebSocket Streaming | ✅ | Auto (5s updates) |
| Prophet Forecasting | ✅ | Predictions → Prophet |
| ARIMA Forecasting | ✅ | Predictions → ARIMA |
| Custom Metrics | ✅ | Admin Panel → Custom Metrics |
| Slack Integration | ✅ | Enable in preferences |
| PagerDuty Alerts | ✅ | Enable in preferences |
| RBAC | ✅ | Admin Panel → User Mgmt |
| Security Audit | ✅ | Run script |

## 🎯 Common Tasks

### Add Email Notifications

1. Configure SMTP in `secrets.toml`
2. Enter email in sidebar
3. Enable "📧 Email Alerts"
4. Click "Test Notifications"

### View Forecasts

1. Click "Predictions" in sidebar
2. Select metric (CPU/Memory/Disk)
3. Choose model (Prophet recommended)
4. Select period (24h default)

### Register Custom Metric

1. Go to "Admin Panel"
2. Click "Custom Metrics" tab
3. Fill in: Name, Description, Code
4. Click "Register"

### Change User Role

1. Go to "Admin Panel"
2. Click "User Management" tab
3. Select role (Admin/Operator/Viewer)
4. Click "Update Role"

## 🐛 Troubleshooting

### Email Not Sending

```bash
# Check SMTP connection
python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com',587); s.starttls(); print('OK')"
```

**Fix**: Use Gmail App Password, not regular password

### WebSocket Disconnected

**Fix**: Restart backend → `python backend/main.py`

### Prophet Not Installing

```bash
# Windows
pip install pystan prophet --no-binary prophet

# Linux/Mac
pip install prophet
```

## 📁 File Structure

```
project/
├── frontend/
│   ├── app.py              # Original (bug-fixed)
│   └── app_enhanced.py     # Production version ⭐
│
├── backend/
│   ├── main.py             # FastAPI app
│   ├── routers/
│   │   └── websocket.py    # WebSocket endpoints
│   └── core/
│       ├── rbac.py         # Access control
│       └── notifications.py # Email/Slack/PagerDuty
│
├── scripts/
│   └── security_audit.py   # Security scanner
│
└── docs/
    ├── PRODUCTION_SETUP.md # Full guide
    └── ENHANCEMENT_SUMMARY.md # Feature list
```

## 🔐 Security Quick Check

```bash
# Run audit
python scripts/security_audit.py

# Expected: 0 critical issues
# ✅ No critical security issues found!
```

## 📞 Quick Reference

| What | Where | URL |
|------|-------|-----|
| Dashboard | Frontend | http://localhost:8501 |
| API Docs | Backend | http://localhost:8000/docs |
| Health Check | Backend | http://localhost:8000/health |
| WebSocket | Backend | ws://localhost:8000/ws |
| Gmail App Passwords | Google | https://myaccount.google.com/apppasswords |
| Slack Webhooks | Slack API | https://api.slack.com/apps |
| PagerDuty Keys | PagerDuty | https://your.pagerduty.com |

## ⚙️ Environment Variables

```env
# Backend (.env)
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True

# Frontend (.streamlit/secrets.toml)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=yourapppassword

SLACK_WEBHOOK_URL=https://hooks.slack.com/...
PAGERDUTY_API_KEY=your_key
PAGERDUTY_SERVICE_KEY=your_service_key
```

## 🎓 Next Steps

1. ✅ Start both backend and frontend
2. ✅ Configure email in secrets.toml
3. ✅ Enter email in sidebar
4. ✅ Test notifications
5. ✅ Explore features:
   - Dashboard → Real-time metrics
   - Predictions → Forecasting
   - Admin Panel → Settings
   - Anomalies → Detection history

## 📚 Full Documentation

- **Setup Guide**: `docs/PRODUCTION_SETUP.md`
- **Feature List**: `ENHANCEMENT_SUMMARY.md`
- **API Docs**: `http://localhost:8000/docs`
- **Original README**: `README.md`

---

**Status**: 🟢 Production Ready  
**Version**: 2.0 Enhanced  
**Last Updated**: November 10, 2025

🎉 **You're all set! Start monitoring your systems in production.**
