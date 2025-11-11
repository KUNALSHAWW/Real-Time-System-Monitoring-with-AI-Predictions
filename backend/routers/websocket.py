"""
Enhanced WebSocket Router for Real-Time Updates with Anomaly Detection
Provides WebSocket endpoint for streaming metrics and anomalies to frontend
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List
import asyncio
import json
from datetime import datetime
import psutil
import numpy as np
from collections import deque

router = APIRouter()

# Store metrics history for anomaly detection
metrics_history = {
    'cpu_percent': deque(maxlen=100),
    'memory_percent': deque(maxlen=100),
    'disk_percent': deque(maxlen=100),
}

# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections[:]:  # Use slice to avoid modification during iteration
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()


def detect_anomaly(metric_name: str, value: float) -> dict:
    """Detect anomaly using Z-score method"""
    if metric_name not in metrics_history:
        metrics_history[metric_name] = deque(maxlen=100)
    
    metrics_history[metric_name].append(value)
    
    # Need at least 10 data points
    if len(metrics_history[metric_name]) < 10:
        return {"is_anomaly": False}
    
    values = list(metrics_history[metric_name])
    mean = np.mean(values)
    std = np.std(values)
    
    if std > 0:
        z_score = abs((value - mean) / std)
    else:
        z_score = 0
    
    is_anomaly = z_score > 2.0
    
    if is_anomaly:
        if z_score > 3.5:
            severity = "critical"
        elif z_score > 3.0:
            severity = "high"
        elif z_score > 2.5:
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "is_anomaly": True,
            "metric_name": metric_name,
            "value": value,
            "z_score": round(z_score, 2),
            "severity": severity,
            "mean": round(mean, 2),
            "std_dev": round(std, 2),
            "threshold": round(mean + 2 * std, 2)
        }
    
    return {"is_anomaly": False}

# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metric streaming with anomaly detection
    
    Streams system metrics every 5 seconds with real-time anomaly detection
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Collect real-time system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            network = psutil.net_io_counters()
            
            # Detect anomalies
            cpu_anomaly = detect_anomaly('cpu_percent', cpu_percent)
            memory_anomaly = detect_anomaly('memory_percent', memory_percent)
            disk_anomaly = detect_anomaly('disk_percent', disk_percent)
            
            anomalies = []
            if cpu_anomaly["is_anomaly"]:
                anomalies.append(cpu_anomaly)
            if memory_anomaly["is_anomaly"]:
                anomalies.append(memory_anomaly)
            if disk_anomaly["is_anomaly"]:
                anomalies.append(disk_anomaly)
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "disk_percent": round(disk_percent, 2),
                "network_sent": network.bytes_sent,
                "network_recv": network.bytes_recv,
                "anomalies": anomalies,
                "has_anomalies": len(anomalies) > 0
            }
            
            # Send metrics to client
            await websocket.send_json(metrics)
            
            # Wait 5 seconds before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert notifications
    
    Streams alerts and anomalies as they are detected
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for client messages (heartbeat)
            data = await websocket.receive_text()
            
            # Echo back (or handle commands)
            await websocket.send_json({
                "status": "connected",
                "message": "Listening for alerts"
            })
            
            await asyncio.sleep(10)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket alerts error: {e}")
        manager.disconnect(websocket)

@router.post("/broadcast/alert")
async def broadcast_alert(alert: dict):
    """
    Broadcast alert to all connected WebSocket clients
    
    This endpoint can be called internally when anomalies are detected
    """
    message = json.dumps({
        "type": "alert",
        "data": alert,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    await manager.broadcast(message)
    
    return {"status": "broadcasted", "connections": len(manager.active_connections)}
