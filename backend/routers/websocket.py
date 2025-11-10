"""
Enhanced WebSocket Router for Real-Time Updates
Provides WebSocket endpoint for streaming metrics to frontend
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List
import asyncio
import json
from datetime import datetime
import psutil

router = APIRouter()

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
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metric streaming
    
    Streams system metrics every 5 seconds to connected clients
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Collect real-time system metrics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_sent": psutil.net_io_counters().bytes_sent,
                "network_recv": psutil.net_io_counters().bytes_recv
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
