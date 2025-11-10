# Quick Start Guide - WebSocket Implementation

## 🚀 Getting Started

### 1. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 3. Verify Backend is Running

Open browser: http://localhost:8000/docs

You should see the FastAPI interactive documentation with all endpoints including:
- `/api/ws/ws` - WebSocket metrics endpoint
- `/api/metrics/*` - Metrics endpoints
- `/api/auth/*` - Authentication endpoints
- etc.

### 4. Test WebSocket Connection (Optional but Recommended)

```bash
cd frontend
python test_websocket.py
```

Expected output:
```
============================================================
 WebSocket Connection Test
============================================================

Attempting to connect to: ws://localhost:8000/api/ws/ws
------------------------------------------------------------
✅ Successfully connected to WebSocket!
Message 1:
  CPU: 45.2%
  Memory: 62.3%
  Disk: 71.5%
  ...
```

### 5. Start the Frontend Dashboard

```bash
cd frontend
streamlit run app.py
```

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### 6. Access the Dashboard

Open browser: http://localhost:8501

You should see:
- ✅ "🟢 API Connection Active" in the sidebar (green indicator)
- ✅ Real-time metrics updating on the Dashboard page
- ✅ CPU, Memory, Disk, and Network metrics
- ✅ Charts showing live data

---

## 📊 Features Now Available

### Real-Time Metrics
- **CPU Usage** - Live percentage and historical chart
- **Memory Usage** - Real-time memory consumption
- **Disk Usage** - Disk space utilization
- **Network I/O** - Bytes sent/received

### Auto-Refresh
- Configurable refresh interval (5-60 seconds)
- Toggle auto-refresh on/off in sidebar
- Smooth updates without manual refresh

### Connection Status
- 🟢 Green: API connection active
- 🟡 Yellow: Demo mode (API unavailable)

---

## 🔧 Configuration

### Change Backend URL

If your backend is running on a different host/port, edit `frontend/app.py`:

```python
API_BASE_URL = "http://localhost:8000"  # Change this
```

### Adjust Default Refresh Interval

Edit `frontend/app.py`:

```python
refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
#                                                                ^^ Change default here
```

---

## 🐛 Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

### Frontend shows "Demo Mode"

**Cause**: Can't connect to backend

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `API_BASE_URL` in `frontend/app.py`
3. Ensure no firewall blocking port 8000

### WebSocket test fails

**Error**: `Connection refused`

**Solutions**:
1. Ensure backend is running
2. Check backend logs for errors
3. Verify WebSocket route is registered in `main.py`

### Dependencies missing

**Error**: `Import "streamlit" could not be resolved`

**Solution**:
```bash
cd frontend
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
project/
├── backend/
│   ├── main.py                 # ✅ Routes initialized
│   ├── requirements.txt
│   └── routers/
│       ├── websocket.py        # ✅ WebSocket endpoints
│       ├── system_metrics.py
│       └── ...
│
├── frontend/
│   ├── app.py                  # ✅ Real-time dashboard
│   ├── metrics_fetcher.py      # ✅ NEW: Metrics polling
│   ├── websocket_client.py     # ✅ NEW: WebSocket client
│   ├── test_websocket.py       # ✅ NEW: WebSocket test
│   ├── WEBSOCKET_GUIDE.md      # ✅ NEW: Documentation
│   └── requirements.txt
│
└── WEBSOCKET_IMPLEMENTATION.md # ✅ NEW: Implementation summary
```

---

## 🎯 Quick Test Checklist

- [ ] Backend starts without errors
- [ ] `/docs` page loads (http://localhost:8000/docs)
- [ ] WebSocket test passes (`python test_websocket.py`)
- [ ] Frontend starts without errors
- [ ] Dashboard shows "🟢 API Connection Active"
- [ ] Metrics update when refreshing page
- [ ] Auto-refresh works with sidebar toggle
- [ ] Charts display live data

---

## 🚀 Next Steps

1. **Explore the Dashboard**: Navigate through different pages (Metrics, Anomalies, Predictions, etc.)

2. **Test Auto-Refresh**: 
   - Check "Auto-refresh" in sidebar
   - Watch metrics update automatically
   - Try different refresh intervals

3. **Monitor Real Data**:
   - Open resource-intensive applications
   - Watch CPU/Memory metrics change
   - Observe network I/O during downloads

4. **Customize**:
   - Modify charts and visualizations
   - Add custom metrics
   - Integrate with your systems

---

## 📚 Additional Resources

- **Full Documentation**: `frontend/WEBSOCKET_GUIDE.md`
- **Implementation Details**: `WEBSOCKET_IMPLEMENTATION.md`
- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **FastAPI WebSocket**: https://fastapi.tiangolo.com/advanced/websockets/
- **Streamlit**: https://docs.streamlit.io/

---

## ✅ Summary

Your WebSocket implementation is complete! The system now supports:

- ✅ Real-time metric streaming from backend
- ✅ Live dashboard with auto-refresh
- ✅ Multiple data fetching methods (polling, WebSocket)
- ✅ Fallback mechanisms for reliability
- ✅ Comprehensive testing tools
- ✅ Production-ready architecture

Enjoy your real-time monitoring dashboard! 🎉
