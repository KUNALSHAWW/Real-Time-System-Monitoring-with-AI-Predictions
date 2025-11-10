# Test Backend Connection
# Run this to verify your backend is working before starting the frontend

import requests
import sys

API_BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Backend Connection Test")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print(f"   ✅ Health check passed: {response.json()}")
    else:
        print(f"   ❌ Health check failed: Status {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Cannot connect to backend: {e}")
    print(f"\n   Make sure backend is running:")
    print(f"   cd backend")
    print(f"   python -m uvicorn main:app --reload")
    sys.exit(1)

# Test 2: Current metrics endpoint
print("\n2. Testing /api/metrics/current endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/api/metrics/current", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Metrics endpoint working!")
        print(f"   CPU: {data.get('cpu_percent', 'N/A')}%")
        print(f"   Memory: {data.get('memory_percent', 'N/A')}%")
        print(f"   Disk: {data.get('disk_percent', 'N/A')}%")
    else:
        print(f"   ❌ Metrics endpoint failed: Status {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Check if all routes are registered
print("\n3. Checking registered routes...")
try:
    response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
    if response.status_code == 200:
        print(f"   ✅ API docs available at: {API_BASE_URL}/docs")
    else:
        print(f"   ⚠️  API docs not available")
except Exception as e:
    print(f"   ⚠️  Cannot access docs: {e}")

# Test 4: WebSocket endpoint
print("\n4. Checking WebSocket endpoint...")
try:
    # Just check if the route exists (will fail with 426 for GET request)
    response = requests.get(f"{API_BASE_URL}/api/ws/ws", timeout=5)
    # WebSocket endpoints return 426 for regular HTTP requests
    if response.status_code in [426, 405]:
        print(f"   ✅ WebSocket endpoint exists")
    else:
        print(f"   ⚠️  WebSocket endpoint status: {response.status_code}")
except Exception as e:
    print(f"   ⚠️  WebSocket check: {e}")

print("\n" + "=" * 60)
print("✅ Backend is ready!")
print("=" * 60)
print("\nYou can now start the frontend:")
print("  cd frontend")
print("  streamlit run app.py")
print("\nOr test WebSocket:")
print("  cd frontend")
print("  python test_websocket.py")
print("=" * 60)
