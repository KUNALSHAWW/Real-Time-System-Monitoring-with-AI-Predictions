# Merged App Guide

## Overview

The new `app_merged.py` combines:
- ✅ **Working backend integration** from `app.py`
- ✅ **Enhanced features** from `app_enhanced.py`
- ✅ All functionalities preserved and merged

## What's Included

### From app.py (Backend Integration)
- ✅ Real backend API connection via `metrics_fetcher.py`
- ✅ `/api/metrics/current` endpoint integration
- ✅ Connection status indicators
- ✅ Fallback to demo data when offline

### From app_enhanced.py (Advanced Features)
- ✅ Email notifications (SMTP)
- ✅ In-app notification center
- ✅ Automated fix suggestions
- ✅ Anomaly detection with alerts
- ✅ User preferences (email, intervals)
- ✅ RBAC (Role-Based Access Control)
- ✅ Admin panel
- ✅ Slack/PagerDuty integration hooks

## How to Use

### Quick Start

```powershell
# 1. Start Backend (Terminal 1)
cd backend
python -m uvicorn main:app --reload

# 2. Test Backend (Terminal 2)
python test_backend.py

# 3. Run Merged App (Terminal 3)
cd frontend
streamlit run app_merged.py
```

### Features

#### 1. Dashboard
- Real-time metrics from your backend
- Automatic anomaly detection
- Alert notifications
- Fix suggestions for issues

#### 2. User Preferences (Sidebar)
- **Email Configuration**: Set your email for alerts
- **Refresh Interval**: Choose update frequency
- **Notification Channels**: Enable/disable email, in-app notifications

#### 3. Notification Center (Sidebar)
- View all notifications
- Unread count badge
- Mark as read functionality

#### 4. Anomaly Detection
- Automatic threshold monitoring
- CPU > 80% triggers alerts
- Memory > 75% triggers alerts
- Disk > 80% triggers alerts

#### 5. Fix Suggestions
Every alert includes:
- Root causes
- Immediate actions
- Shell commands to run
- Step-by-step guides

#### 6. Admin Panel (Requires admin role)
- User role management
- Alert threshold configuration
- System settings

## Configuration

### Email Notifications

To enable email alerts, create `.streamlit/secrets.toml`:

```toml
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
```

### Backend URL

Change in `app_merged.py`:
```python
API_BASE_URL = "http://localhost:8000"  # Update if different
```

### Alert Thresholds

Default thresholds in code:
- CPU: 80%
- Memory: 75%
- Disk: 80%

Can be changed in Admin Panel (admin role required).

## User Roles

### Viewer (Default)
- View dashboard and metrics
- Receive notifications
- Cannot modify settings

### Operator
- All viewer permissions
- Create incidents
- Acknowledge alerts

### Admin
- All operator permissions
- Access admin panel
- Change user roles
- Modify system config

To change role, go to **Admin Panel** → **User Management** (requires admin access initially).

## Features Breakdown

### ✅ Preserved from app.py
- Backend API integration
- Real metrics from `/api/metrics/current`
- Connection status checking
- Metrics history buffering
- Auto-refresh mechanism

### ✅ Added from app_enhanced.py
- Email notification system
- In-app notification center
- Automated fix suggestions
- Anomaly detection engine
- User preference management
- RBAC system
- Admin panel
- Security features (input validation, sanitization)

### ✅ Enhanced/Improved
- Combined notification center
- Better error handling
- Graceful fallback when backend offline
- Integrated alert history
- Unified configuration

## Testing Checklist

- [ ] Backend connects successfully
- [ ] Real metrics display on dashboard
- [ ] Metrics update automatically
- [ ] Anomaly alerts trigger correctly
- [ ] In-app notifications appear
- [ ] Email notifications send (if configured)
- [ ] Fix suggestions display
- [ ] Admin panel accessible (admin role)
- [ ] User preferences save correctly

## Troubleshooting

### No Real Metrics
**Issue**: Shows demo data instead of real metrics

**Fix**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check connection status in sidebar
3. Click "Test Connection" in Backend Info expander

### Email Notifications Not Sending
**Issue**: Emails not received

**Fix**:
1. Configure SMTP credentials in `.streamlit/secrets.toml`
2. Enable email notifications in User Preferences
3. Set valid email address
4. Check SMTP server allows connections

### Anomalies Not Detected
**Issue**: No alerts trigger

**Fix**:
1. Wait for metrics to exceed thresholds (CPU > 80%, Memory > 75%, Disk > 80%)
2. Check alert history is initializing correctly
3. Ensure notification preferences are enabled

### Admin Panel Access Denied
**Issue**: Cannot access admin panel

**Fix**:
1. Default role is 'viewer'
2. Temporarily change code to set initial role:
   ```python
   'user_role': 'admin',  # Change from 'viewer'
   ```
3. Or use Admin Panel to change your own role (chicken-egg problem - needs initial admin)

## Advantages of Merged App

1. **Single Source of Truth**: One app with all features
2. **Backend Integration**: Works with real data when available
3. **Graceful Degradation**: Falls back to demo mode offline
4. **Production Ready**: Includes notifications, RBAC, security
5. **User Friendly**: Comprehensive UI with preferences
6. **Maintainable**: Clean code structure, well documented

## Migration from Old Apps

### From app.py
No changes needed - `app_merged.py` is a superset

### From app_enhanced.py  
All features included, plus:
- Real backend integration
- Better connection handling
- Working metrics fetcher

## Next Steps

1. **Test thoroughly**: Run through all features
2. **Configure email**: Set up SMTP for alerts
3. **Customize thresholds**: Adjust in Admin Panel
4. **Add users**: If multi-user, implement user management
5. **Deploy**: Use `app_merged.py` for production

## Files

- `app_merged.py` - Merged application (use this!)
- `app.py` - Original with backend integration (backup)
- `app_enhanced.py` - Original with enhanced features (backup)
- `metrics_fetcher.py` - Backend API client (required)
- `test_backend.py` - Backend connection tester

---

**Recommendation**: Use `app_merged.py` as your main application going forward!
