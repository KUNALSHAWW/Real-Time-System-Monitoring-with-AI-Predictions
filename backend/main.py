"""
Real-Time System Monitoring with AI Predictions — SaaS Backend
Main application entry point with async DB lifecycle.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers import (
    system_metrics,
    anomaly_detection,
    predictions,
    authentication,
    incidents,
    ai_analysis,
    websocket,
    reports,
    cost_analysis,
)
from routers.ingest import router as ingest_router

from core.database import init_db, close_db
from core.config import settings


# ---------------------------------------------------------------------------
# App lifespan — initialise / tear down the database
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logging.info("Initialising database…")
    await init_db()
    yield
    # --- Shutdown ---
    await close_db()


app = FastAPI(
    title="Real-Time System Monitoring with AI Predictions",
    description="Multi-tenant SaaS backend — receives metrics from remote agents, "
                "runs ML anomaly detection, and streams alerts over WebSocket.",
    version="2.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

cors_origins = (
    settings.cors_origins
    if getattr(settings, "ENVIRONMENT", "development") == "production"
    else ["http://localhost:3000"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# Auth (no JWT required on login/register)
app.include_router(
    authentication.router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

# Agent data ingestion (API-key auth)
app.include_router(
    ingest_router,
    prefix="/api/v1/metrics",
    tags=["Metrics Ingestion"],
)

# Authenticated metric retrieval
app.include_router(
    system_metrics.router,
    prefix="/api/v1/metrics",
    tags=["System Metrics"],
)

app.include_router(
    anomaly_detection.router,
    prefix="/api/v1/anomalies",
    tags=["Anomaly Detection"],
)

app.include_router(
    predictions.router,
    prefix="/api/v1/predictions",
    tags=["Predictions"],
)

app.include_router(
    incidents.router,
    prefix="/api/v1/incidents",
    tags=["Incidents"],
)

app.include_router(
    ai_analysis.router,
    prefix="/api/v1/ai",
    tags=["AI Analysis"],
)

app.include_router(
    reports.router,
    prefix="/api/v1/reports",
    tags=["Email Reports"],
)

app.include_router(
    cost_analysis.router,
    prefix="/api/v1/cost",
    tags=["Cost Analysis"],
)

# WebSocket (per-agent alert & metric streams)
app.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"],
)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    return {
        "message": "Real-Time System Monitoring SaaS API",
        "version": "2.0.0",
        "docs": "/docs",
    }
