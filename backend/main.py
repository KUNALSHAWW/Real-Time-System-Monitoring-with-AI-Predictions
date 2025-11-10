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
# from routers import (
#     system_metrics,
#     anomaly_detection,
#     predictions,
#     authentication,
#     incidents,
#     ai_analysis
# )
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

app = FastAPI(title="Test App")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Main app running"}


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
