from fastapi import FastAPI

app = FastAPI(title="Test App")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Test app running"}