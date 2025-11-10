"""
Test WebSocket Connection to Backend
Run this script to verify WebSocket connectivity
"""

import asyncio
import websockets
import json
from datetime import datetime


async def test_websocket():
    """Test WebSocket connection to backend"""
    
    ws_url = "ws://localhost:8000/api/ws/ws"
    print(f"Attempting to connect to: {ws_url}")
    print("-" * 60)
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Successfully connected to WebSocket!")
            print(f"Connection established at: {datetime.now()}")
            print("-" * 60)
            print("\nReceiving real-time metrics...\n")
            
            # Receive first 10 messages
            for i in range(10):
                try:
                    # Receive message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    
                    # Parse JSON
                    metrics = json.loads(message)
                    
                    # Display metrics
                    print(f"Message {i + 1}:")
                    print(f"  Timestamp: {metrics.get('timestamp', 'N/A')}")
                    print(f"  CPU: {metrics.get('cpu_percent', 0):.1f}%")
                    print(f"  Memory: {metrics.get('memory_percent', 0):.1f}%")
                    print(f"  Disk: {metrics.get('disk_percent', 0):.1f}%")
                    print(f"  Network Sent: {metrics.get('network_sent', 0):,} bytes")
                    print(f"  Network Recv: {metrics.get('network_recv', 0):,} bytes")
                    print("-" * 60)
                    
                except asyncio.TimeoutError:
                    print("⚠️  Timeout waiting for message")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing JSON: {e}")
                    print(f"   Raw message: {message}")
                    
            print("\n✅ Test completed successfully!")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure the backend server is running")
        print("2. Check that the backend is listening on localhost:8000")
        print("3. Verify the WebSocket route is properly configured")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def test_alerts_websocket():
    """Test alerts WebSocket endpoint"""
    
    ws_url = "ws://localhost:8000/api/ws/ws/alerts"
    print(f"\nTesting alerts WebSocket: {ws_url}")
    print("-" * 60)
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to alerts WebSocket!")
            
            # Send heartbeat
            await websocket.send("heartbeat")
            
            # Receive response
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            print(f"Response: {data}")
            
            print("✅ Alerts WebSocket test completed!")
            
    except Exception as e:
        print(f"❌ Error testing alerts WebSocket: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print(" WebSocket Connection Test")
    print("=" * 60)
    print()
    
    # Test main metrics WebSocket
    asyncio.run(test_websocket())
    
    # Test alerts WebSocket
    asyncio.run(test_alerts_websocket())
    
    print("\n" + "=" * 60)
    print(" Test completed")
    print("=" * 60)
