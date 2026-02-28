"""
System Metrics Router — serves historical metric data from the database.

All local psutil collection has been removed.  Metrics now arrive
exclusively from remote agents via POST /api/v1/metrics/ingest.

Every endpoint requires JWT authentication and scopes results to the
authenticated user's agents.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_deps import get_current_user
from core.database import get_db
from core.models import Agent, MetricRecord, User
from core.logger import get_logger

logger = get_logger("metrics")
router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------

class MetricDataPoint(BaseModel):
    timestamp: str
    value: float
    unit: str
    agent_id: str


class MetricsResponse(BaseModel):
    metric_name: str
    data_points: List[MetricDataPoint]
    count: int
    timestamp: str


class AgentSummary(BaseModel):
    agent_id: str
    is_active: bool
    last_seen_at: Optional[str]


class CurrentSnapshot(BaseModel):
    agent_id: str
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    disk_write_bytes_delta: int
    disk_read_bytes_delta: int
    network_sent_bytes_delta: int
    network_recv_bytes_delta: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_metric_series(
    db: AsyncSession,
    user_id: str,
    agent_id: Optional[str],
    column_name: str,
    unit: str,
    hours: int,
) -> MetricsResponse:
    """
    Generic helper — query metric_records for a given column, filtered by
    user, optional agent, and time-range.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    col = getattr(MetricRecord, column_name)

    stmt = (
        select(MetricRecord.timestamp, col, MetricRecord.agent_id)
        .where(MetricRecord.user_id == user_id, MetricRecord.timestamp >= cutoff)
    )
    if agent_id:
        stmt = stmt.where(MetricRecord.agent_id == agent_id)
    stmt = stmt.order_by(MetricRecord.timestamp.asc())

    result = await db.execute(stmt)
    rows = result.all()

    data_points = [
        MetricDataPoint(
            timestamp=row[0].isoformat(),
            value=round(float(row[1]), 2) if row[1] is not None else 0.0,
            unit=unit,
            agent_id=row[2],
        )
        for row in rows
    ]

    return MetricsResponse(
        metric_name=column_name,
        data_points=data_points,
        count=len(data_points),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/agents", response_model=List[AgentSummary])
async def list_agents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all agents belonging to the authenticated user."""
    result = await db.execute(
        select(Agent).where(Agent.user_id == user.id).order_by(Agent.created_at)
    )
    agents = result.scalars().all()
    return [
        AgentSummary(
            agent_id=a.agent_id,
            is_active=a.is_active,
            last_seen_at=a.last_seen_at.isoformat() if a.last_seen_at else None,
        )
        for a in agents
    ]


@router.get("/cpu", response_model=MetricsResponse)
async def get_cpu_metrics(
    hours: int = Query(1, ge=1, le=24),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """CPU utilisation history for the authenticated user's agent(s)."""
    return await _get_metric_series(db, user.id, agent_id, "cpu_percent", "%", hours)


@router.get("/memory", response_model=MetricsResponse)
async def get_memory_metrics(
    hours: int = Query(1, ge=1, le=24),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Memory utilisation history."""
    return await _get_metric_series(db, user.id, agent_id, "memory_percent", "%", hours)


@router.get("/disk", response_model=MetricsResponse)
async def get_disk_metrics(
    hours: int = Query(1, ge=1, le=24),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disk utilisation history."""
    return await _get_metric_series(db, user.id, agent_id, "disk_percent", "%", hours)


@router.get("/network", response_model=MetricsResponse)
async def get_network_metrics(
    hours: int = Query(1, ge=1, le=24),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Network bytes sent (delta) history."""
    return await _get_metric_series(
        db, user.id, agent_id, "network_sent_bytes_delta", "bytes", hours
    )


@router.get("/history")
async def get_metrics_history(
    minutes: int = Query(60, ge=1, le=1440),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Raw metric history (all columns) for the given time range."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    stmt = (
        select(MetricRecord)
        .where(MetricRecord.user_id == user.id, MetricRecord.timestamp >= cutoff)
    )
    if agent_id:
        stmt = stmt.where(MetricRecord.agent_id == agent_id)
    stmt = stmt.order_by(MetricRecord.timestamp.asc())

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {
        "data_points": [
            {
                "timestamp": r.timestamp.isoformat(),
                "agent_id": r.agent_id,
                "cpu_percent": r.cpu_percent,
                "memory_percent": r.memory_percent,
                "disk_percent": r.disk_percent,
                "disk_write_bytes_delta": r.disk_write_bytes_delta,
                "disk_read_bytes_delta": r.disk_read_bytes_delta,
                "network_sent_bytes_delta": r.network_sent_bytes_delta,
                "network_recv_bytes_delta": r.network_recv_bytes_delta,
            }
            for r in rows
        ],
        "count": len(rows),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/current", response_model=List[CurrentSnapshot])
async def get_current_metrics(
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the *latest* metric snapshot for each of the user's agents.
    If ``agent_id`` is provided, return only that agent's latest reading.
    """
    # Sub-query: latest timestamp per agent
    sub = (
        select(
            MetricRecord.agent_id,
            func.max(MetricRecord.timestamp).label("max_ts"),
        )
        .where(MetricRecord.user_id == user.id)
        .group_by(MetricRecord.agent_id)
    )
    if agent_id:
        sub = sub.where(MetricRecord.agent_id == agent_id)
    sub = sub.subquery()

    stmt = (
        select(MetricRecord)
        .join(
            sub,
            (MetricRecord.agent_id == sub.c.agent_id)
            & (MetricRecord.timestamp == sub.c.max_ts),
        )
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        CurrentSnapshot(
            agent_id=r.agent_id,
            timestamp=r.timestamp.isoformat(),
            cpu_percent=r.cpu_percent,
            memory_percent=r.memory_percent,
            disk_percent=r.disk_percent,
            disk_write_bytes_delta=r.disk_write_bytes_delta or 0,
            disk_read_bytes_delta=r.disk_read_bytes_delta or 0,
            network_sent_bytes_delta=r.network_sent_bytes_delta or 0,
            network_recv_bytes_delta=r.network_recv_bytes_delta or 0,
        )
        for r in rows
    ]
