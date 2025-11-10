# SETUP AND TESTING GUIDE

## Quick Start (Step by Step)

### Step 1: Start the Backend

Open PowerShell/Terminal and run:

```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Test the Backend

Open a NEW PowerShell/Terminal and run:

```powershell
python test_backend.py
```

Expected output:
```
============================================================
Backend Connection Test
============================================================

1. Testing health endpoint...
   ✅ Health check passed: {'status': 'healthy'}

2. Testing /api/metrics/current endpoint...
   ✅ Metrics endpoint working!
   CPU: 45.2%
   Memory: 62.3%
   Disk: 71.5%

3. Checking registered routes...
   ✅ API docs available at: http://localhost:8000/docs

4. Checking WebSocket endpoint...
   ✅ WebSocket endpoint exists

============================================================
✅ Backend is ready!
============================================================
```

If you see errors, make sure:
- Backend is running (Step 1)
- No firewall blocking port 8000
- Python dependencies are installed: `cd backend; pip install -r requirements.txt`

### Step 3: Start the Frontend

Open a NEW PowerShell/Terminal and run:

```powershell
cd frontend
streamlit run app.py
```

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Step 4: Verify Connection

1. Open browser: http://localhost:8501
2. Look at the sidebar - you should see: **"🟢 Connected to Backend"**
3. The metrics should show REAL data from your system, not random values
4. Click "Test Connection" in the sidebar's "Backend Info" expander

## Troubleshooting

### Issue: "🔴 Demo Mode" or "🟠 Backend Offline"

**Cause**: Frontend cannot connect to backend

**Solutions**:

1. **Verify backend is running:**
   ```powershell
   # In your browser, open:
   http://localhost:8000/health
   
   # Should show:
   {"status":"healthy"}
   ```

2. **Check the backend URL in frontend:**
   - Open `frontend/app.py`
   - Find line with `API_BASE_URL = "http://localhost:8000"`
   - Make sure it matches your backend address

3. **Test connection manually:**
   ```powershell
   python test_backend.py
   ```

4. **Check backend logs** for errors in the terminal where you started it

### Issue: Backend won't start

**Error**: `ModuleNotFoundError` or import errors

**Solution**:
```powershell
cd backend
pip install -r requirements.txt
```

**Error**: `Address already in use` or port 8000 is busy

**Solution**:
```powershell
# Use a different port:
python -m uvicorn main:app --reload --port 8001

# Then update frontend/app.py:
# API_BASE_URL = "http://localhost:8001"
```

### Issue: Frontend shows errors

**Error**: `Import "streamlit" could not be resolved`

**Solution**:
```powershell
cd frontend
pip install -r requirements.txt
```

### Issue: Metrics not updating

1. **Check auto-refresh is enabled** (checkbox in sidebar)
2. **Adjust refresh interval** (slider in sidebar)
3. **Manually refresh** the page (F5 or browser refresh)

## Testing WebSocket (Optional)

```powershell
cd frontend
python test_websocket.py
```

Expected output:
```
✅ Successfully connected to WebSocket!
Message 1:
  CPU: 45.2%
  Memory: 62.3%
  Disk: 71.5%
  ...
```

## What's Working Now

✅ **Backend** has `/api/metrics/current` endpoint that returns real-time metrics
✅ **Frontend** fetches metrics from backend every 5-60 seconds (configurable)
✅ **Connection status** shown in sidebar
✅ **Fallback mode** with demo data if backend is offline
✅ **Real metrics** from your actual system using `psutil`

## API Endpoints Available

Once backend is running, visit: **http://localhost:8000/docs**

You'll see:
- `GET /health` - Health check
- `GET /api/metrics/current` - Current real-time metrics ⭐ NEW
- `GET /api/metrics/cpu` - CPU historical data
- `GET /api/metrics/memory` - Memory historical data
- `GET /api/metrics/disk` - Disk historical data
- `GET /api/metrics/network` - Network historical data
- `WS /api/ws/ws` - WebSocket for streaming metrics
- And many more...

## Next Steps

1. **Verify it's working**: Watch the metrics update in the dashboard
2. **Customize refresh rate**: Use the sidebar slider
3. **Explore other pages**: Metrics, Anomalies, Predictions, etc.
4. **Add more features**: Customize the dashboard as needed

## Directory Structure

```
project/
├── backend/
│   ├── main.py                 # ✅ All routes registered
│   └── routers/
│       ├── system_metrics.py   # ✅ /current endpoint added
│       └── websocket.py        # ✅ WebSocket streaming
│
├── frontend/
│   ├── app.py                  # ✅ Enhanced with connection status
│   ├── metrics_fetcher.py      # ✅ Calls /current endpoint
│   └── test_websocket.py       # For testing WebSocket
│
└── test_backend.py             # ✅ NEW: Test backend connectivity
```

## Running Everything at Once

### Option 1: Three Terminals

**Terminal 1** (Backend):
```powershell
cd backend
python -m uvicorn main:app --reload
```

**Terminal 2** (Test - Optional):
```powershell
python test_backend.py
```

**Terminal 3** (Frontend):
```powershell
cd frontend
streamlit run app.py
```

### Option 2: Using Docker Compose (if configured)

```powershell
docker-compose up
```

## Success Checklist

- [ ] Backend starts without errors
- [ ] `test_backend.py` shows all ✅ checkmarks
- [ ] Frontend starts and opens in browser
- [ ] Sidebar shows "🟢 Connected to Backend"
- [ ] CPU/Memory/Disk metrics show real values (not same every time)
- [ ] Metrics update when you refresh the page
- [ ] Auto-refresh works (metrics change automatically)

## Support

If you're still having issues:

1. Check both terminal outputs for error messages
2. Verify Python version: `python --version` (should be 3.8+)
3. Ensure all dependencies are installed
4. Check firewall isn't blocking localhost connections
5. Try using 127.0.0.1 instead of localhost in `API_BASE_URL`

---

**Your system is now ready for real-time monitoring!** 🎉
