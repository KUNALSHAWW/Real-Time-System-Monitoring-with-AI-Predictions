"""
Predictions Router — per-agent forecasting using Moving Average on DB data.

All endpoints require JWT authentication and scope results to the
authenticated user's agents.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_deps import get_current_user
from core.database import get_db
from core.models import MetricRecord, User
from core.logger import get_logger

logger = get_logger("predictions")
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class Prediction(BaseModel):
    timestamp: str
    predicted_value: float
    confidence: float


class PredictionResponse(BaseModel):
    metric_name: str
    agent_id: str
    current_value: float
    predictions: List[Prediction]
    next_anomaly_probability: float
    explanation: str
    data_points_used: int
    timestamp: str


# ---------------------------------------------------------------------------
# Forecast helpers (same algorithm, now per-agent DB data)
# ---------------------------------------------------------------------------

def _moving_average_forecast(
    data: List[float], window: int = 10, steps: int = 12
) -> List[tuple[float, float]]:
    if len(data) < window:
        window = max(len(data), 1)
    ma = np.convolve(data, np.ones(window) / window, mode="valid")
    if len(ma) == 0:
        return [(float(np.mean(data)), 0.5)] * steps

    recent = ma[-min(20, len(ma)):]
    trend = (recent[-1] - recent[0]) / len(recent) if len(recent) > 1 else 0
    std_dev = float(np.std(data[-window:]) if len(data) >= window else np.std(data))
    last_value = float(ma[-1])

    forecasts: list[tuple[float, float]] = []
    for i in range(steps):
        predicted = last_value + trend * (i + 1) * 0.8
        predicted = max(0.0, min(100.0, predicted))
        confidence = max(0.3, 1.0 - i * 0.05 - std_dev / 50)
        forecasts.append((round(predicted, 2), round(confidence, 2)))
    return forecasts


def _anomaly_probability(data: List[float], threshold: float = 90.0) -> float:
    if len(data) < 5:
        return 0.1
    recent = data[-20:]
    trend = (recent[-1] - recent[0]) / len(recent) if len(recent) > 1 else 0
    current = recent[-1]
    dist = (threshold - current) / threshold

    if current >= threshold:
        prob = 0.9
    elif trend > 0 and current > threshold * 0.7:
        prob = min(0.8, 0.3 + trend * 10 + (1 - dist) * 0.3)
    else:
        prob = max(0.05, 0.2 - dist * 0.1 + float(np.std(recent)) / 100)
    return round(min(0.95, max(0.05, prob)), 2)


def _explain(metric: str, current: float, forecasts: List[float], prob: float) -> str:
    avg = float(np.mean(forecasts)) if forecasts else current
    trend = "stable"
    if len(forecasts) > 1:
        if forecasts[-1] > forecasts[0] * 1.05:
            trend = "increasing"
        elif forecasts[-1] < forecasts[0] * 0.95:
            trend = "decreasing"
    risk = "low" if prob < 0.3 else "medium" if prob < 0.6 else "high"
    note = {
        "high": "Attention needed: Values may exceed safe limits soon.",
        "low": "System looks healthy for the next hour.",
        "medium": "Monitor closely — moderate risk detected.",
    }[risk]
    return (
        f"{metric} Forecast — Current: {current:.1f}% | Predicted avg: {avg:.1f}% "
        f"| Trend: {trend} | Risk: {risk.upper()} — {note}"
    )


# ---------------------------------------------------------------------------
# DB helper — fetch per-agent metric column
# ---------------------------------------------------------------------------

async def _fetch_series(
    db: AsyncSession, user_id: str, agent_id: str, column: str, limit: int = 200
) -> List[float]:
    col = getattr(MetricRecord, column, None)
    if col is None:
        raise HTTPException(400, f"Unknown metric column: {column}")
    stmt = (
        select(col)
        .where(MetricRecord.user_id == user_id, MetricRecord.agent_id == agent_id)
        .order_by(MetricRecord.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    # oldest-first for forecasting
    return [float(r[0]) for r in reversed(result.all()) if r[0] is not None]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/forecast/{metric_name}", response_model=PredictionResponse)
async def forecast_metric(
    metric_name: str,
    agent_id: str = Query(...),
    hours: int = Query(1, ge=1, le=24),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Moving-average forecast for a metric on a specific agent."""
    column = f"{metric_name}_percent"
    values = await _fetch_series(db, user.id, agent_id, column)

    if len(values) < 2:
        return PredictionResponse(
            metric_name=metric_name,
            agent_id=agent_id,
            current_value=values[-1] if values else 0,
            predictions=[],
            next_anomaly_probability=0.1,
            explanation="Not enough historical data yet.",
            data_points_used=len(values),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    steps = hours * 12
    forecasts = _moving_average_forecast(values, steps=steps)
    now = datetime.now(timezone.utc)

    preds = [
        Prediction(
            timestamp=(now + timedelta(minutes=(i + 1) * 5)).isoformat(),
            predicted_value=pv,
            confidence=c,
        )
        for i, (pv, c) in enumerate(forecasts)
    ]
    fvals = [f[0] for f in forecasts]
    current = values[-1]
    prob = _anomaly_probability(values)

    return PredictionResponse(
        metric_name=metric_name,
        agent_id=agent_id,
        current_value=round(current, 2),
        predictions=preds,
        next_anomaly_probability=prob,
        explanation=_explain(metric_name.upper(), current, fvals, prob),
        data_points_used=len(values),
        timestamp=now.isoformat(),
    )


@router.get("/anomaly-risk")
async def get_anomaly_risk(
    agent_id: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Anomaly risk probability per metric for a specific agent."""
    risks = {}
    for metric in ("cpu", "memory", "disk"):
        col = f"{metric}_percent"
        values = await _fetch_series(db, user.id, agent_id, col)
        if len(values) >= 5:
            risks[metric] = {
                "current": round(values[-1], 2),
                "probability": _anomaly_probability(values),
                "trend": (
                    "increasing"
                    if len(values) > 5 and values[-1] > values[-5]
                    else "stable"
                ),
            }

    max_risk = max((r["probability"] for r in risks.values()), default=0)
    level = "high" if max_risk > 0.7 else "medium" if max_risk > 0.4 else "low"

    return {
        "agent_id": agent_id,
        "risk_level": level,
        "overall_probability": round(max_risk, 2),
        "metrics_risk": risks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/alerts/predictive")
async def get_predictive_alerts(
    agent_id: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Predictive alerts for a specific agent over the next 30 min."""
    alerts: list[dict] = []
    for metric in ("cpu", "memory", "disk"):
        col = f"{metric}_percent"
        values = await _fetch_series(db, user.id, agent_id, col)
        if len(values) < 5:
            continue
        prob = _anomaly_probability(values)
        current = values[-1]
        if prob > 0.5 or current > 75:
            forecasts = _moving_average_forecast(values, steps=6)
            max_fc = max(f[0] for f in forecasts)
            if max_fc > 85 or prob > 0.6:
                alerts.append({
                    "metric": metric,
                    "severity": "high" if max_fc > 90 else "medium",
                    "current_value": round(current, 2),
                    "predicted_max": round(max_fc, 2),
                    "probability": prob,
                    "message": f"{metric.upper()} predicted to reach {max_fc:.1f}% in the next 30 minutes",
                })

    return {
        "agent_id": agent_id,
        "alerts": alerts,
        "total": len(alerts),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
