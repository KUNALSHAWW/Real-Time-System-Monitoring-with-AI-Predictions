"""
Real-Time System Monitoring with AI Predictions - Backend API
Main application entry point
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
# import uvicorn
# from dotenv import load_dotenv

# Load environment variables FIRST
# load_dotenv()

# Import routers and utilities
from routers import (
    system_metrics,
    anomaly_detection,
    predictions,
    authentication,
    incidents,
    ai_analysis,
    websocket
)
# from core.database import init_db, get_db
# from core.config import settings
# from core.state_manager import StateManager
# from core.logger import setup_logging
# from middleware.logging_middleware import LoggingMiddleware
# from middleware.error_handler import error_handler_middleware

# Setup logging
# logger = setup_logging()

# Initialize state manager
# state_manager = StateManager()

app = FastAPI(
    title="Real-Time System Monitoring with AI Predictions",
    description="Backend API for real-time system monitoring with AI-powered predictions and anomaly detection",
    version="1.0.0"
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ROUTERS
# ============================================================================

# Include all routers with appropriate prefixes and tags
app.include_router(
    authentication.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    system_metrics.router,
    prefix="/api/metrics",
    tags=["System Metrics"]
)

app.include_router(
    anomaly_detection.router,
    prefix="/api/anomalies",
    tags=["Anomaly Detection"]
)

app.include_router(
    predictions.router,
    prefix="/api/predictions",
    tags=["Predictions"]
)

app.include_router(
    incidents.router,
    prefix="/api/incidents",
    tags=["Incidents"]
)

app.include_router(
    ai_analysis.router,
    prefix="/api/ai",
    tags=["AI Analysis"]
)

app.include_router(
    websocket.router,
    prefix="/api/ws",
    tags=["WebSocket"]
)

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "message": "Real-Time System Monitoring API",
        "version": "1.0.0",
        "status": "running"
    }


# ============================================================================
# ENTRY POINT
# ============================================================================

# if __name__ == "__main__":
#     logger.info("Starting Real-Time System Monitoring Backend")
    
#     uvicorn.run(
#         app,
#         host=settings.BACKEND_HOST,
#         port=settings.BACKEND_PORT,
#         log_level=settings.LOG_LEVEL.lower(),
#         access_log=True,
#         reload=settings.DEBUG
#     )
