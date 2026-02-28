"""
Anomaly Detection Router — per-agent anomaly detection using the ML engine.

All endpoints require JWT authentication and scope results to the
authenticated user's agents.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_deps import get_current_user
from core.database import get_db
from core.models import AnomalyEvent, MetricRecord, User
from core.logger import get_logger

logger = get_logger("anomalies")
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AnomalyOut(BaseModel):
    id: int
    agent_id: str
    timestamp: str
    metric_name: str
    value: float
    z_score: Optional[float]
    severity: str
    message: Optional[str]
    acknowledged: bool


class AnomalyListResponse(BaseModel):
    total_anomalies: int
    anomalies: List[AnomalyOut]
    timestamp: str


class DetectRequest(BaseModel):
    agent_id: str
    metric_name: str
    value: float


# ---------------------------------------------------------------------------
# Helpers — Z-score anomaly detection against per-agent history
# ---------------------------------------------------------------------------

async def _detect_zscore(
    db: AsyncSession,
    user_id: str,
    agent_id: str,
    metric_name: str,
    value: float,
) -> dict:
    """
    Compute a Z-score for *value* against the last 100 readings for
    the given agent + metric.
    """
    col = getattr(MetricRecord, metric_name, None)
    if col is None:
        raise HTTPException(400, f"Unknown metric: {metric_name}")

    stmt = (
        select(col)
        .where(
            MetricRecord.user_id == user_id,
            MetricRecord.agent_id == agent_id,
        )
        .order_by(MetricRecord.timestamp.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    history = [float(r[0]) for r in result.all() if r[0] is not None]

    if len(history) < 10:
        return {"is_anomaly": False, "message": "Collecting baseline data…"}

    mean = float(np.mean(history))
    std = float(np.std(history))
    z_score = abs((value - mean) / std) if std > 0 else 0.0

    is_anomaly = z_score > 2.0
    severity = (
        "critical" if z_score > 3.5
        else "high" if z_score > 3.0
        else "medium" if z_score > 2.5
        else "low"
    )

    return {
        "is_anomaly": is_anomaly,
        "metric_name": metric_name,
        "value": value,
        "z_score": round(z_score, 2),
        "severity": severity,
        "mean": round(mean, 2),
        "std_dev": round(std, 2),
        "threshold": round(mean + 2 * std, 2),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/detect")
async def detect_anomaly_realtime(
    body: DetectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run real-time Z-score anomaly detection on a single data point
    using the specific agent's historical baseline (not global data).
    """
    result = await _detect_zscore(db, user.id, body.agent_id, body.metric_name, body.value)
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    return result


@router.get("/list", response_model=AnomalyListResponse)
async def list_anomalies(
    hours: int = Query(1, ge=1, le=168),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List anomaly events recorded for this user's agents.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(AnomalyEvent)
        .where(AnomalyEvent.user_id == user.id, AnomalyEvent.timestamp >= cutoff)
    )
    if severity:
        stmt = stmt.where(AnomalyEvent.severity == severity)
    if agent_id:
        stmt = stmt.where(AnomalyEvent.agent_id == agent_id)
    stmt = stmt.order_by(AnomalyEvent.timestamp.desc()).limit(500)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return AnomalyListResponse(
        total_anomalies=len(rows),
        anomalies=[
            AnomalyOut(
                id=r.id,
                agent_id=r.agent_id,
                timestamp=r.timestamp.isoformat(),
                metric_name=r.metric_name,
                value=r.value,
                z_score=r.z_score,
                severity=r.severity,
                message=r.message,
                acknowledged=r.acknowledged,
            )
            for r in rows
        ],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/metrics/{metric_name}")
async def get_metric_anomalies(
    metric_name: str,
    hours: int = Query(1, ge=1, le=168),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get anomalies for a specific metric across the user's agents."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(AnomalyEvent)
        .where(
            AnomalyEvent.user_id == user.id,
            AnomalyEvent.metric_name == metric_name,
            AnomalyEvent.timestamp >= cutoff,
        )
    )
    if agent_id:
        stmt = stmt.where(AnomalyEvent.agent_id == agent_id)
    stmt = stmt.order_by(AnomalyEvent.timestamp.desc()).limit(200)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {
        "metric_name": metric_name,
        "anomalies": [
            {
                "agent_id": r.agent_id,
                "timestamp": r.timestamp.isoformat(),
                "value": r.value,
                "severity": r.severity,
                "z_score": r.z_score,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/analyze")
async def analyze_for_anomalies(
    body: DetectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyse a single data point for the given agent (same as /detect but
    with a friendlier name kept for backwards compat).
    """
    return await detect_anomaly_realtime(body, user, db)
