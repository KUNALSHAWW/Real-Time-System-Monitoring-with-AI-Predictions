"""
WebSocket Client for Real-Time Metrics
Handles WebSocket connection to backend and data streaming
"""

import asyncio
import json
import websockets
from typing import Optional, Callable, Dict, Any
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsWebSocketClient:
    """WebSocket client for real-time system metrics"""
    
    def __init__(self, ws_url: str = "ws://localhost:8000/api/ws/ws"):
        self.ws_url = ws_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.callback: Optional[Callable] = None
        
    def set_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback function to handle received metrics"""
        self.callback = callback
    
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            logger.info(f"Connected to WebSocket: {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from WebSocket")
    
    async def receive_metrics(self):
        """Receive and process metrics from WebSocket"""
        if not self.websocket:
            logger.warning("WebSocket not connected")
            return
        
        try:
            while self.is_connected:
                # Receive message from WebSocket
                message = await self.websocket.recv()
                
                # Parse JSON data
                metrics = json.loads(message)
                
                # Add client-side timestamp if not present
                if 'client_received_at' not in metrics:
                    metrics['client_received_at'] = datetime.now().isoformat()
                
                # Call callback if set
                if self.callback:
                    self.callback(metrics)
                
                logger.debug(f"Received metrics: {metrics}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error receiving metrics: {e}")
            self.is_connected = False
    
    async def run(self):
        """Main run loop - connect and receive metrics"""
        connected = await self.connect()
        
        if connected:
            await self.receive_metrics()
        else:
            logger.error("Failed to start WebSocket client")


# Example usage function
async def example_usage():
    """Example of how to use the WebSocket client"""
    
    def on_metrics_received(metrics: Dict[str, Any]):
        """Callback function to handle received metrics"""
        print(f"CPU: {metrics.get('cpu_percent', 0):.1f}%")
        print(f"Memory: {metrics.get('memory_percent', 0):.1f}%")
        print(f"Disk: {metrics.get('disk_percent', 0):.1f}%")
        print("-" * 50)
    
    # Create client
    client = MetricsWebSocketClient()
    client.set_callback(on_metrics_received)
    
    # Run client
    try:
        await client.run()
    except KeyboardInterrupt:
        await client.disconnect()
        print("Client stopped")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
