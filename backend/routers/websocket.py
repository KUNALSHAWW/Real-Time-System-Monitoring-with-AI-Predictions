"""
WebSocket Router — per-agent real-time alert streaming.

Endpoints:
  WS  /ws/alerts/{agent_id}  — subscribe to anomaly alerts for a specific agent
  WS  /ws/metrics/{agent_id} — subscribe to live metric push for a specific agent
  POST /broadcast/alert       — internal helper to push an alert to subscribers
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.logger import get_logger

logger = get_logger("websocket")
router = APIRouter()


# ---------------------------------------------------------------------------
# Connection Manager — keyed by agent_id
# ---------------------------------------------------------------------------

class AgentConnectionManager:
    """
    Manages WebSocket connections per agent_id.
    Each agent_id has its own subscriber list.
    """

    def __init__(self) -> None:
        # agent_id → list of websockets
        self._alert_subs: Dict[str, List[WebSocket]] = {}
        self._metric_subs: Dict[str, List[WebSocket]] = {}

    # -- alert subscriptions ------------------------------------------------

    async def connect_alerts(self, agent_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._alert_subs.setdefault(agent_id, []).append(ws)
        logger.info("Alert subscriber connected for agent '%s' (total=%d)",
                     agent_id, len(self._alert_subs[agent_id]))

    def disconnect_alerts(self, agent_id: str, ws: WebSocket) -> None:
        conns = self._alert_subs.get(agent_id, [])
        if ws in conns:
            conns.remove(ws)

    async def push_alerts(self, agent_id: str, payload: dict | list) -> int:
        """Send an alert payload to all subscribers of *agent_id*. Returns delivery count."""
        conns = self._alert_subs.get(agent_id, [])
        sent = 0
        message = json.dumps({
            "type": "alert",
            "agent_id": agent_id,
            "data": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        for ws in conns[:]:
            try:
                await ws.send_text(message)
                sent += 1
            except Exception:
                conns.remove(ws)
        return sent

    # -- metric subscriptions -----------------------------------------------

    async def connect_metrics(self, agent_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._metric_subs.setdefault(agent_id, []).append(ws)
        logger.info("Metrics subscriber connected for agent '%s'", agent_id)

    def disconnect_metrics(self, agent_id: str, ws: WebSocket) -> None:
        conns = self._metric_subs.get(agent_id, [])
        if ws in conns:
            conns.remove(ws)

    async def push_metrics(self, agent_id: str, payload: dict) -> int:
        """Send a metric snapshot to all subscribers of *agent_id*."""
        conns = self._metric_subs.get(agent_id, [])
        sent = 0
        message = json.dumps({
            "type": "metrics",
            "agent_id": agent_id,
            "data": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        for ws in conns[:]:
            try:
                await ws.send_text(message)
                sent += 1
            except Exception:
                conns.remove(ws)
        return sent

    # -- broadcast to ALL agent subscribers ---------------------------------

    async def broadcast_all(self, payload: dict) -> int:
        """Broadcast a message to every connected subscriber regardless of agent."""
        sent = 0
        message = json.dumps(payload)
        for conns in list(self._alert_subs.values()) + list(self._metric_subs.values()):
            for ws in conns[:]:
                try:
                    await ws.send_text(message)
                    sent += 1
                except Exception:
                    conns.remove(ws)
        return sent


manager = AgentConnectionManager()


# ---------------------------------------------------------------------------
# Public helper — called by the ingest router to push alerts
# ---------------------------------------------------------------------------

async def push_alert(agent_id: str, anomalies: list[dict]) -> int:
    """Push anomaly alerts through the WebSocket for this agent."""
    return await manager.push_alerts(agent_id, anomalies)


async def push_metric(agent_id: str, metric_snapshot: dict) -> int:
    """Push a live metric snapshot through the WebSocket for this agent."""
    return await manager.push_metrics(agent_id, metric_snapshot)


# ---------------------------------------------------------------------------
# WebSocket endpoints
# ---------------------------------------------------------------------------

@router.websocket("/alerts/{agent_id}")
async def ws_alerts(websocket: WebSocket, agent_id: str):
    """
    Subscribe to anomaly / critical alerts for a specific agent.

    The server pushes messages of the form:
        { "type": "alert", "agent_id": "...", "data": [...], "timestamp": "..." }

    The client may send text frames as keep-alive pings.
    """
    await manager.connect_alerts(agent_id, websocket)
    try:
        while True:
            # Keep the connection alive; accept pings from the client
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_alerts(agent_id, websocket)
        logger.info("Alert subscriber disconnected for agent '%s'", agent_id)
    except Exception as exc:
        manager.disconnect_alerts(agent_id, websocket)
        logger.warning("WS alerts error for '%s': %s", agent_id, exc)


@router.websocket("/metrics/{agent_id}")
async def ws_metrics(websocket: WebSocket, agent_id: str):
    """
    Subscribe to live metric snapshots for a specific agent.
    Metrics are pushed each time the agent's data is ingested.
    """
    await manager.connect_metrics(agent_id, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_metrics(agent_id, websocket)
    except Exception as exc:
        manager.disconnect_metrics(agent_id, websocket)
        logger.warning("WS metrics error for '%s': %s", agent_id, exc)


# ---------------------------------------------------------------------------
# REST helper — broadcast alert (backwards compatible internal endpoint)
# ---------------------------------------------------------------------------

@router.post("/broadcast/alert")
async def broadcast_alert(alert: dict):
    """Broadcast an alert to ALL connected WebSocket subscribers."""
    sent = await manager.broadcast_all({
        "type": "alert",
        "data": alert,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "broadcasted", "delivered_to": sent}
