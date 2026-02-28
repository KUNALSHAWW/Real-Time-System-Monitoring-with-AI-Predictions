"""
Metrics Ingestion Router — receives data from remote agents.

POST /api/v1/metrics/ingest
  - Validates the X-API-Key header
  - Persists the incoming payload to the database
  - Auto-registers the agent if it's new
  - Runs anomaly detection per-agent and pushes alerts over WebSocket
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_deps import require_api_key
from core.database import get_db
from core.models import Agent, MetricRecord, User
from core.logger import get_logger

logger = get_logger("ingest")
router = APIRouter()


# --------------------------------------------------------------------------
# Request / Response schemas
# --------------------------------------------------------------------------

class MetricPayload(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=128)
    timestamp: Optional[str] = None

    # CPU
    cpu_percent: float = Field(..., ge=0, le=100)
    cpu_freq_mhz: Optional[float] = None

    # Memory
    memory_percent: float = Field(..., ge=0, le=100)
    memory_used_bytes: Optional[int] = None
    memory_total_bytes: Optional[int] = None

    # Disk
    disk_percent: float = Field(..., ge=0, le=100)
    disk_used_bytes: Optional[int] = None
    disk_total_bytes: Optional[int] = None

    # Disk I/O deltas
    disk_read_bytes_delta: int = 0
    disk_write_bytes_delta: int = 0
    disk_read_count_delta: int = 0
    disk_write_count_delta: int = 0

    # Network
    network_sent_bytes_delta: int = 0
    network_recv_bytes_delta: int = 0
    network_sent_bytes_total: int = 0
    network_recv_bytes_total: int = 0


class IngestResponse(BaseModel):
    status: str = "ok"
    agent_id: str
    recorded_at: str
    anomalies: list = []


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------

@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest_metrics(
    payload: MetricPayload,
    user: User = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive a metric snapshot from a remote agent.

    • Authenticates via `X-API-Key` header.
    • Auto-creates the Agent row on first contact.
    • Persists the metric record.
    • Runs lightweight anomaly detection and returns any alerts.
    """

    # --- resolve / auto-register agent ------------------------------------
    result = await db.execute(
        select(Agent).where(
            Agent.user_id == user.id,
            Agent.agent_id == payload.agent_id,
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        agent = Agent(
            agent_id=payload.agent_id,
            user_id=user.id,
        )
        db.add(agent)
        await db.flush()          # get the generated PK
        logger.info("Auto-registered new agent '%s' for user '%s'",
                     payload.agent_id, user.username)

    # Update last-seen timestamp
    agent.last_seen_at = datetime.now(timezone.utc)
    agent.is_active = True

    # --- parse timestamp --------------------------------------------------
    ts = datetime.now(timezone.utc)
    if payload.timestamp:
        try:
            ts = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
        except ValueError:
            pass  # fall back to server time

    # --- persist metric record --------------------------------------------
    record = MetricRecord(
        agent_pk=agent.id,
        user_id=user.id,
        agent_id=payload.agent_id,
        timestamp=ts,
        cpu_percent=payload.cpu_percent,
        cpu_freq_mhz=payload.cpu_freq_mhz,
        memory_percent=payload.memory_percent,
        memory_used_bytes=payload.memory_used_bytes,
        memory_total_bytes=payload.memory_total_bytes,
        disk_percent=payload.disk_percent,
        disk_used_bytes=payload.disk_used_bytes,
        disk_total_bytes=payload.disk_total_bytes,
        disk_read_bytes_delta=payload.disk_read_bytes_delta,
        disk_write_bytes_delta=payload.disk_write_bytes_delta,
        disk_read_count_delta=payload.disk_read_count_delta,
        disk_write_count_delta=payload.disk_write_count_delta,
        network_sent_bytes_delta=payload.network_sent_bytes_delta,
        network_recv_bytes_delta=payload.network_recv_bytes_delta,
        network_sent_bytes_total=payload.network_sent_bytes_total,
        network_recv_bytes_total=payload.network_recv_bytes_total,
    )
    db.add(record)
    await db.commit()

    # --- inline quick anomaly check (per-agent) ---------------------------
    anomalies = _quick_anomaly_check(payload)

    # Push anomalies to WebSocket manager (non-blocking, best-effort)
    if anomalies:
        try:
            from routers.websocket import push_alert
            await push_alert(payload.agent_id, anomalies)
        except Exception as exc:
            logger.warning("Failed to push WS alert: %s", exc)

    return IngestResponse(
        agent_id=payload.agent_id,
        recorded_at=ts.isoformat(),
        anomalies=anomalies,
    )


# --------------------------------------------------------------------------
# Quick threshold-based anomaly check (runs per-agent payload)
# --------------------------------------------------------------------------

_THRESHOLDS = {
    # Only fire on genuinely dangerous levels — not normal dev-machine usage
    "cpu_percent":            {"high": 95, "critical": 99},     # sustained 95%+ is real trouble
    "memory_percent":         {"high": 96, "critical": 99},     # 96%+ means swapping / OOM risk
    "disk_percent":           {"high": 93, "critical": 98},     # near-full disk = real risk
    "disk_write_bytes_delta": {"high": 500_000_000, "critical": 1_000_000_000},  # 500 MB / 1 GB per interval
}


def _quick_anomaly_check(payload: MetricPayload) -> list[dict]:
    """Return a list of anomaly dicts for any metric exceeding thresholds.
    
    Only fires for genuinely dangerous conditions — NOT normal high usage.
    """
    anomalies: list[dict] = []
    data = payload.model_dump()

    for metric, bounds in _THRESHOLDS.items():
        value = data.get(metric)
        if value is None:
            continue
        if value >= bounds["critical"]:
            severity = "critical"
        elif value >= bounds["high"]:
            severity = "high"
        else:
            continue

        label = metric.replace("_", " ").replace("percent", "").strip().upper()

        if severity == "critical":
            if metric == "disk_write_bytes_delta":
                msg = (
                    f"CRITICAL: Abnormal Disk Write Activity ({value / 1_000_000:.0f} MB/interval) "
                    f"— possible ransomware, bulk encryption, or runaway process on {payload.agent_id}"
                )
            elif metric == "memory_percent":
                msg = f"CRITICAL: Memory at {value:.1f}% — system may be swapping/OOM on {payload.agent_id}"
            elif metric == "cpu_percent":
                msg = f"CRITICAL: CPU at {value:.1f}% — sustained full load on {payload.agent_id}"
            else:
                msg = f"CRITICAL: {label} at {value:.1f}% on {payload.agent_id}"
        else:
            if metric == "disk_write_bytes_delta":
                msg = f"WARNING: High disk write rate ({value / 1_000_000:.0f} MB/interval) on {payload.agent_id}"
            else:
                msg = f"WARNING: {label} at {value:.1f}% on {payload.agent_id} — approaching critical"

        anomalies.append({
            "metric": metric,
            "value": value,
            "severity": severity,
            "message": msg,
            "agent_id": payload.agent_id,
        })

    return anomalies
