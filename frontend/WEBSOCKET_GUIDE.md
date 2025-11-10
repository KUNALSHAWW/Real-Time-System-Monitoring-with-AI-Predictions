# WebSocket Implementation Guide

## Overview

The frontend now supports real-time metric updates through multiple methods:
1. **Polling via REST API** (Default, most reliable with Streamlit)
2. **WebSocket Client** (For standalone scripts)
3. **Auto-refresh** (Streamlit native approach)

## Architecture

### Backend WebSocket Routes
Located in `backend/routers/websocket.py`:

- **`/api/ws/ws`** - Real-time system metrics stream
  - Sends metrics every 5 seconds
  - Includes: CPU, Memory, Disk, Network stats
  
- **`/api/ws/ws/alerts`** - Real-time alert notifications
  - Streams alerts as they occur
  - Supports heartbeat messages

### Frontend Implementation

#### 1. Streamlit Dashboard (`app.py`)
Uses polling approach for reliability:
- Fetches metrics via `MetricsFetcher` class
- Caches data in session state
- Auto-refreshes page at configurable intervals

#### 2. WebSocket Client (`websocket_client.py`)
Standalone WebSocket client for direct connection:
```python
from websocket_client import MetricsWebSocketClient

client = MetricsWebSocketClient("ws://localhost:8000/api/ws/ws")
client.set_callback(lambda metrics: print(metrics))
await client.run()
```

#### 3. Metrics Fetcher (`metrics_fetcher.py`)
Streamlit-optimized polling client:
```python
from metrics_fetcher import MetricsFetcher, fetch_and_cache_metrics

fetcher = MetricsFetcher("http://localhost:8000")
metrics = fetch_and_cache_metrics(fetcher)
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Frontend dependencies
cd frontend
pip install -r requirements.txt
```

### 2. Start Backend Server

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test WebSocket Connection

```bash
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

### 4. Run Streamlit Dashboard

```bash
cd frontend
streamlit run app.py
```

## Configuration

### Backend Configuration

Edit `backend/core/config.py`:
```python
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8000
```

### Frontend Configuration

Edit `frontend/app.py`:
```python
API_BASE_URL = "http://localhost:8000"  # Change to your backend URL
```

## Troubleshooting

### WebSocket Connection Fails

**Problem**: `ConnectionRefusedError` or `WebSocket connection failed`

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check WebSocket endpoint: `curl http://localhost:8000/api/ws/ws` (should fail with method not allowed)
3. Ensure no firewall blocking port 8000
4. Check backend logs for errors

### No Real-Time Updates

**Problem**: Dashboard shows "Demo Mode" or stale data

**Solutions**:
1. Verify `metrics_fetcher.py` is in the same directory as `app.py`
2. Check API connection: Open `http://localhost:8000/docs` in browser
3. Enable debug mode in Streamlit to see errors
4. Check browser console for JavaScript errors

### CORS Issues

**Problem**: WebSocket connection blocked by CORS

**Solution**: Add CORS middleware in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Features

### Real-Time Metrics Display
- ✅ CPU utilization
- ✅ Memory usage
- ✅ Disk usage
- ✅ Network I/O
- ✅ Historical charts

### Auto-Refresh Options
1. **Streamlit native** - Page rerun (default)
2. **streamlit-autorefresh** - Smooth refresh without full reload
3. **Manual refresh** - Disable auto-refresh in sidebar

### Fallback Mechanisms
- API unavailable → Simulated demo data
- WebSocket closed → Falls back to polling
- Network error → Uses cached data

## Performance Optimization

### Metrics Buffer
- Stores last 100 data points in memory
- Uses `deque` for efficient FIFO operations
- Cached with `@st.cache_resource`

### API Rate Limiting
- Default: 1 request per refresh interval
- Configurable via sidebar slider (5-60 seconds)

### Data Compression
For high-frequency updates, consider:
- Backend: Use msgpack instead of JSON
- Frontend: Implement data downsampling

## Production Deployment

### Backend
```bash
# Use production ASGI server
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
# Run Streamlit in production mode
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Docker Deployment
Both backend and frontend have Dockerfiles configured. Use:
```bash
docker-compose up -d
```

## API Endpoints Reference

### REST API
- `GET /api/metrics/current` - Current metrics snapshot
- `GET /api/metrics/{metric_name}` - Historical data
- `GET /health` - Health check

### WebSocket
- `WS /api/ws/ws` - Real-time metrics stream
- `WS /api/ws/ws/alerts` - Real-time alerts
- `POST /api/ws/broadcast/alert` - Broadcast alert to all clients

## Testing

### Unit Tests
```bash
# Test WebSocket client
python frontend/test_websocket.py

# Test metrics fetcher
python -m pytest frontend/test_metrics_fetcher.py
```

### Integration Tests
```bash
# Test end-to-end flow
python scripts/test_e2e.py
```

## Known Limitations

1. **Streamlit Threading**: Background WebSocket threads don't work reliably with Streamlit's execution model
2. **Browser Compatibility**: WebSocket support required (IE11 not supported)
3. **Reconnection**: Manual page refresh needed after backend restart

## Future Enhancements

- [ ] Automatic reconnection with exponential backoff
- [ ] Binary protocol (msgpack/protobuf) for efficiency
- [ ] Multi-host monitoring support
- [ ] Custom metric subscriptions
- [ ] Alert filtering and routing

## Support

For issues or questions:
1. Check backend logs: `backend/logs/`
2. Enable Streamlit debug mode: `streamlit run app.py --logger.level=debug`
3. Review WebSocket test output
4. Check API documentation: `http://localhost:8000/docs`
