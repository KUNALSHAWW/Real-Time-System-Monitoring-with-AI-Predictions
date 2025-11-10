from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Startup')
    yield
    print('Shutdown')

app = FastAPI(lifespan=lifespan)

@app.get('/test')
async def test():
    return {'status': 'ok'}