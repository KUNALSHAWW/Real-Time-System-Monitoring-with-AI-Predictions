# 🚀 Production Setup Guide

## Overview
This guide walks you through setting up the enhanced production-grade system monitoring platform with all advanced features.

## ✨ New Features Added

### 1. **Security Enhancements**
- ✅ Input validation and sanitization
- ✅ CSRF token protection
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ Advanced RBAC (Admin, Operator, Viewer roles)
- ✅ Security audit script

### 2. **WebSocket Real-Time Updates**
- ✅ Live metric streaming (5-second intervals)
- ✅ Real-time alert notifications
- ✅ Automatic connection management

### 3. **Advanced Forecasting**
- ✅ Facebook Prophet integration
- ✅ ARIMA time-series forecasting
- ✅ Model comparison and selection

### 4. **Multi-Channel Notifications**
- ✅ **Email**: SMTP with HTML templates and suggested fixes
- ✅ **In-App**: Real-time notification center
- ✅ **Slack**: Webhook integration with color-coded alerts
- ✅ **PagerDuty**: Incident management integration

### 5. **Custom Metric Plugins**
- ✅ Plugin architecture for extensibility
- ✅ Dynamic metric registration
- ✅ Custom visualization support

### 6. **Enhanced UI Features**
- ✅ Email input on main page
- ✅ Configurable check intervals (5s to 1 hour)
- ✅ Notification preference management
- ✅ In-app notification center
- ✅ Admin panel for configuration

## 📋 Prerequisites

- Python 3.12+ (or 3.9-3.11)
- Docker & Docker Compose (optional)
- PostgreSQL 13+
- Redis 7+
- InfluxDB 2.0+ (optional)

## 🔧 Installation Steps

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key new dependencies:
- `websockets==12.0` - WebSocket support
- `psutil==5.9.6` - System metrics
- `prophet` - Advanced forecasting (will be in ml_engine)
- `statsmodels` - ARIMA forecasting

### Step 2: Install Frontend Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

New dependencies:
- `prophet` - Facebook Prophet forecasting
- `statsmodels` - Statistical models
- `websockets` - WebSocket client

### Step 3: Configure Secrets

Create a `.streamlit/secrets.toml` file in the frontend directory:

```toml
# Email/SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"

# Slack Integration
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# PagerDuty Integration
PAGERDUTY_API_KEY = "your_pagerduty_api_key"
PAGERDUTY_SERVICE_KEY = "your_pagerduty_service_key"
```

**Note**: For Gmail, you need to:
1. Enable 2FA on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password (not your regular password)

### Step 4: Run Security Audit

```bash
python scripts/security_audit.py
```

This will check for:
- Hardcoded secrets
- SQL injection vulnerabilities
- XSS risks
- Weak cryptography
- CORS misconfigurations
- Missing rate limiting
- Input validation issues

### Step 5: Start Backend with WebSocket Support

```bash
cd backend
python main.py
```

The backend will start on:
- HTTP: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws`

### Step 6: Start Enhanced Frontend

```bash
cd frontend
streamlit run app_enhanced.py
```

Or run the original (now fixed):
```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 🔐 Setting Up Notifications

### Email Notifications (SMTP)

1. **Gmail Setup**:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Use the 16-character app password in secrets.toml

2. **Other SMTP Providers**:
   - **Outlook**: `smtp-mail.outlook.com:587`
   - **Yahoo**: `smtp.mail.yahoo.com:587`
   - **SendGrid**: `smtp.sendgrid.net:587`

### Slack Notifications

1. Go to https://api.slack.com/apps
2. Create a new app
3. Enable "Incoming Webhooks"
4. Create a webhook for your channel
5. Copy the webhook URL to secrets.toml

### PagerDuty Integration

1. Log in to PagerDuty: https://your-domain.pagerduty.com
2. Go to Configuration → API Access
3. Create a new API key
4. Create a new service integration
5. Copy both keys to secrets.toml

## 🎯 Usage Guide

### 1. User Preferences (Sidebar)

On the main page sidebar, configure:

- **Email Address**: Enter your email to receive alerts
- **Check Interval**: Select how often to monitor (5s to 1 hour)
- **Notification Channels**: 
  - ✅ Email Alerts
  - ✅ In-App Notifications
  - ✅ Slack Notifications
  - ✅ PagerDuty Alerts

Click "Test Notifications" to verify your setup.

### 2. Notification Center

Click the notification bell 🔔 in the sidebar to view:
- Recent alerts
- Unread notification count
- Alert history

### 3. Admin Panel (Admin Role Only)

Access the Admin Panel to:
- Manage user roles (Admin, Operator, Viewer)
- Configure integrations (SMTP, Slack, PagerDuty)
- Register custom metric plugins
- Adjust system configuration

### 4. Advanced Forecasting

In the Predictions page:
1. Select metric to forecast
2. Choose forecast period (6h, 12h, 24h, 48h)
3. Select model:
   - **Prophet**: Best for seasonal patterns
   - **ARIMA**: Best for trend analysis
   - **Simple Moving Average**: Fast baseline

### 5. Real-Time WebSocket Updates

The dashboard automatically connects via WebSocket to receive:
- Live metric updates every 5 seconds
- Real-time alert notifications
- System health changes

Connection status is shown in the sidebar.

## 🔒 RBAC - Role Permissions

### Admin
- Full access to all features
- Can manage users and roles
- Can delete data
- Can modify system settings

### Operator
- Can view all metrics
- Can create/update incidents
- Can trigger manual alerts
- Cannot manage users or delete data

### Viewer
- Read-only access to metrics
- Can view incidents
- Cannot modify anything

## 📧 Email Alert Example

When an anomaly is detected, you'll receive:

**Subject**: 🚨 ALERT: CPU Usage Anomaly Detected

**Body**:
```
System Monitoring Alert

Metric: CPU Usage
Current Value: 87.5%
Threshold: 80.0%
Severity: CRITICAL
Timestamp: 2025-11-10 12:30:45

🔧 Suggested Fixes:
1. Check system resource utilization
2. Review recent changes or deployments
3. Investigate potential memory leaks or CPU-intensive processes
4. Scale resources if needed

View dashboard: http://localhost:8501
```

## 🧪 Testing

### Test Email Notifications

```python
from backend.core.notifications import EmailService
import asyncio

email_service = EmailService(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your_email@gmail.com",
    password="your_app_password"
)

asyncio.run(email_service.send_email(
    to_email="recipient@example.com",
    subject="Test Email",
    body="This is a test",
    suggested_fixes=["Fix 1", "Fix 2"]
))
```

### Test Slack Notifications

```python
from backend.core.notifications import SlackService
import asyncio

slack = SlackService(webhook_url="your_webhook_url")

asyncio.run(slack.send_notification(
    message="Test alert from system monitor",
    severity="warning"
))
```

### Run Security Audit

```bash
python scripts/security_audit.py
```

Expected output:
```
🔒 Starting Security Audit...
============================================================

📋 Checking for hardcoded secrets...
  ✓ Checked for hardcoded secrets
📋 Checking for SQL injection risks...
  ✓ Checked for SQL injection vulnerabilities
...

============================================================
🔒 SECURITY AUDIT REPORT
============================================================

📊 Summary:
  🔴 Critical Issues: 0
  🟡 Warnings: 3
  🔵 Info: 5
  📈 Total Findings: 8

✅ No critical security issues found!
============================================================
```

## 🚢 Deployment

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up -d
```

Services started:
- PostgreSQL (port 5432)
- Redis (port 6379)
- InfluxDB (port 8086)
- Backend API (port 8000)
- Frontend Dashboard (port 8501)

### Option 2: Manual Deployment

1. Set up production environment variables
2. Use Gunicorn for backend:
   ```bash
   gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
3. Use production WSGI server for Streamlit:
   ```bash
   streamlit run frontend/app_enhanced.py --server.port 8501 --server.address 0.0.0.0
   ```

## 📊 Monitoring Production

### Health Checks

- Backend health: `http://localhost:8000/health`
- Detailed health: `http://localhost:8000/health/detailed`
- API docs: `http://localhost:8000/docs`

### Metrics

- Prometheus metrics: `http://localhost:9090/metrics`
- WebSocket status: Check sidebar in dashboard

## 🐛 Troubleshooting

### Email Not Sending

1. Check SMTP credentials in secrets.toml
2. Verify Gmail App Password (not regular password)
3. Check firewall allows port 587
4. Test with: `telnet smtp.gmail.com 587`

### Slack Notifications Failing

1. Verify webhook URL is correct
2. Check webhook is active in Slack app settings
3. Test webhook with curl:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test"}' \
     YOUR_WEBHOOK_URL
   ```

### WebSocket Not Connecting

1. Check backend is running on port 8000
2. Verify WebSocket endpoint: `ws://localhost:8000/ws`
3. Check browser console for connection errors
4. Try: `wscat -c ws://localhost:8000/ws`

### Prophet Installation Issues

```bash
# On Windows, may need:
pip install prophet --no-binary prophet

# On Linux/Mac:
pip install prophet
```

## 📈 Performance Optimization

1. **Enable Redis Caching**: Set `REDIS_HOST` in .env
2. **Adjust Check Interval**: Higher intervals reduce load
3. **Limit Notification Channels**: Disable unused channels
4. **Use WebSocket**: More efficient than polling
5. **Database Connection Pooling**: Configure in settings

## 🔐 Security Best Practices

1. ✅ Never commit `.env` or `secrets.toml` to git
2. ✅ Use strong, unique passwords for all services
3. ✅ Enable HTTPS in production
4. ✅ Implement rate limiting on API endpoints
5. ✅ Regularly update dependencies
6. ✅ Run security audits before deployment
7. ✅ Use environment-specific configurations
8. ✅ Enable authentication for all endpoints
9. ✅ Sanitize all user inputs
10. ✅ Use RBAC to limit access

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [WebSocket RFC](https://tools.ietf.org/html/rfc6455)
- [OWASP Security Guidelines](https://owasp.org/)

## 🆘 Support

If you encounter issues:

1. Check logs: `backend/logs/app.log`
2. Run security audit: `python scripts/security_audit.py`
3. Verify all services are running: `docker-compose ps`
4. Check environment variables are set correctly
5. Review API documentation: `http://localhost:8000/docs`

---

**Version**: 2.0 (Production Enhanced)  
**Last Updated**: November 10, 2025  
**Status**: ✅ Production Ready
