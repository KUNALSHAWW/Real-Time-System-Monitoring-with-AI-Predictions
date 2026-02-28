"""
Incidents Router — incident tracking and management.

Auto-incident creation from local psutil has been REMOVED.
Incidents are now created either:
  1. Automatically by the ingest pipeline when anomalies are detected.
  2. Manually via POST /create.

All list/stats endpoints are kept in-memory for now (migrate to DB as needed).
"""

from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from core.auth_deps import get_current_user
from core.models import User
from core.logger import get_logger
import uuid
import threading

logger = get_logger("incidents")
router = APIRouter()

# ============================================================================
# IN-MEMORY INCIDENT STORAGE (per-user incidents — will migrate to DB)
# ============================================================================

INCIDENTS: List[dict] = []
INCIDENTS_LOCK = threading.Lock()

# Thresholds for auto-incident creation
CPU_THRESHOLD = 90.0
MEMORY_THRESHOLD = 90.0
DISK_THRESHOLD = 95.0


class IncidentStatus(str, Enum):
    """Incident status values"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(BaseModel):
    """Incident record"""
    id: str
    title: str
    description: str
    status: IncidentStatus
    severity: str
    metric_type: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    agent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assignee: Optional[str] = None
    auto_generated: bool = False


class CreateIncidentRequest(BaseModel):
    """Request to create a new incident"""
    title: str
    description: str
    severity: str = "medium"
    assignee: Optional[str] = None
    agent_id: Optional[str] = None


def generate_incident_id() -> str:
    """Generate unique incident ID"""
    return f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


# ---- Public helper — called by the ingest pipeline on anomalies ---------

def create_auto_incident(
    agent_id: str,
    metric_type: str,
    metric_value: float,
    threshold: float,
    severity: str = "critical",
):
    """Create an auto-generated incident from the ingest anomaly pipeline."""
    title = f"CRITICAL: {metric_type} at {metric_value:.1f}% on {agent_id}"
    description = (
        f"{metric_type} utilisation exceeded {threshold}% threshold. "
        f"Current: {metric_value:.1f}% (agent: {agent_id})"
    )
    with INCIDENTS_LOCK:
        # De-duplicate: skip if there's already an open incident for this agent + metric
        for inc in INCIDENTS:
            if (
                inc["agent_id"] == agent_id
                and inc["metric_type"] == metric_type
                and inc["status"] in ("open", "investigating")
                and inc.get("auto_generated")
            ):
                inc["metric_value"] = metric_value
                inc["updated_at"] = datetime.now(timezone.utc).isoformat()
                return
        INCIDENTS.append({
            "id": generate_incident_id(),
            "title": title,
            "description": description,
            "status": "open",
            "severity": severity,
            "metric_type": metric_type,
            "metric_value": metric_value,
            "threshold": threshold,
            "agent_id": agent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "assignee": None,
            "auto_generated": True,
        })
        logger.warning("Auto-created incident: %s", title)


@router.get("/list")
async def list_incidents(
    status: str = Query("all", pattern="^(open|investigating|resolved|closed|all)$"),
    agent_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """List incidents, optionally filtered by status and agent_id."""
    logger.info("Fetching incidents for user=%s status=%s agent=%s", user.id, status, agent_id)

    with INCIDENTS_LOCK:
        results = INCIDENTS
        if status != "all":
            results = [inc for inc in results if inc["status"] == status]
        if agent_id:
            results = [inc for inc in results if inc.get("agent_id") == agent_id]
        return sorted(results, key=lambda x: x["created_at"], reverse=True)


@router.get("/stats")
async def get_incident_stats(user: User = Depends(get_current_user)):
    """Get incident statistics."""
    with INCIDENTS_LOCK:
        total = len(INCIDENTS)
        open_count = len([i for i in INCIDENTS if i["status"] == "open"])
        investigating = len([i for i in INCIDENTS if i["status"] == "investigating"])
        resolved = len([i for i in INCIDENTS if i["status"] == "resolved"])
        auto_generated = len([i for i in INCIDENTS if i.get("auto_generated", False)])

    return {
        "total": total,
        "open": open_count,
        "investigating": investigating,
        "resolved": resolved,
        "closed": total - open_count - investigating - resolved,
        "auto_generated": auto_generated,
        "thresholds": {
            "cpu": CPU_THRESHOLD,
            "memory": MEMORY_THRESHOLD,
            "disk": DISK_THRESHOLD,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/create")
async def create_incident(
    request: CreateIncidentRequest,
    user: User = Depends(get_current_user),
):
    """Create a new incident manually."""
    logger.info("Creating incident: %s (user=%s)", request.title, user.id)
    now = datetime.now(timezone.utc).isoformat()
    new_incident = {
        "id": generate_incident_id(),
        "title": request.title,
        "description": request.description,
        "status": "open",
        "severity": request.severity,
        "metric_type": None,
        "metric_value": None,
        "threshold": None,
        "agent_id": request.agent_id,
        "created_at": now,
        "updated_at": now,
        "assignee": request.assignee,
        "auto_generated": False,
    }
    with INCIDENTS_LOCK:
        INCIDENTS.append(new_incident)
    return new_incident


@router.put("/update/{incident_id}")
async def update_incident(
    incident_id: str,
    status: Optional[str] = None,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    severity: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """Update an incident."""
    logger.info("Updating incident: %s (user=%s)", incident_id, user.id)
    with INCIDENTS_LOCK:
        for incident in INCIDENTS:
            if incident["id"] == incident_id:
                if status:
                    incident["status"] = status
                if description:
                    incident["description"] = description
                if assignee:
                    incident["assignee"] = assignee
                if severity:
                    incident["severity"] = severity
                incident["updated_at"] = datetime.now(timezone.utc).isoformat()
                return incident
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


@router.delete("/delete/{incident_id}")
async def delete_incident(
    incident_id: str,
    user: User = Depends(get_current_user),
):
    """Delete an incident."""
    logger.info("Deleting incident: %s (user=%s)", incident_id, user.id)
    with INCIDENTS_LOCK:
        for i, incident in enumerate(INCIDENTS):
            if incident["id"] == incident_id:
                deleted = INCIDENTS.pop(i)
                return {"message": f"Incident {incident_id} deleted", "incident": deleted}
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


@router.post("/resolve/{incident_id}")
async def resolve_incident(
    incident_id: str,
    resolution_notes: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """Resolve an incident."""
    logger.info("Resolving incident: %s (user=%s)", incident_id, user.id)
    with INCIDENTS_LOCK:
        for incident in INCIDENTS:
            if incident["id"] == incident_id:
                incident["status"] = "resolved"
                incident["updated_at"] = datetime.now(timezone.utc).isoformat()
                if resolution_notes:
                    incident["description"] += f"\n\nResolution: {resolution_notes}"
                return incident
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
