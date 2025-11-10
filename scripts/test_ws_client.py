import asyncio
import json

try:
    import websockets
except ImportError:
    print('websockets package not installed')
    raise

async def main():
    uri = 'ws://localhost:8000/ws'
    try:
        async with websockets.connect(uri) as ws:
            print('Connected to', uri)
            msg = await ws.recv()
            try:
                data = json.loads(msg)
                print('Received JSON message:')
                print(json.dumps(data, indent=2))
            except Exception:
                print('Received message:', msg)
    except Exception as e:
        print('WebSocket connection failed:', str(e))

if __name__ == '__main__':
    asyncio.run(main())
