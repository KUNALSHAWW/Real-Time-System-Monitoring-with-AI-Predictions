#!/usr/bin/env python3
"""
Lightweight Agent Sensor — runs on the user's local machine.

Collects CPU, Memory, Disk, Network, and Disk-I/O metrics via psutil
and POSTs them as JSON to the central SaaS monitoring server every
few seconds.  Configuration is read from a local .env file.

Usage:
    pip install -r requirements.txt
    cp .env.example .env   # edit values
    python sensor.py
"""

from __future__ import annotations

import os
import sys
import time
import signal
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psutil
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()  # read .env in the same directory (or parent)

SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000").rstrip("/")
USER_API_KEY: str = os.getenv("USER_API_KEY", "")
AGENT_ID: str = os.getenv("AGENT_ID", "default-agent")
COLLECTION_INTERVAL: int = int(os.getenv("COLLECTION_INTERVAL", "5"))

INGEST_ENDPOINT = f"{SERVER_URL}/api/v1/metrics/ingest"

# Clamp interval between 2 and 60 seconds
COLLECTION_INTERVAL = max(2, min(60, COLLECTION_INTERVAL))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("agent")

# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

_running = True


def _handle_signal(signum: int, _frame: Any) -> None:
    global _running
    log.info("Received signal %s — shutting down.", signal.Signals(signum).name)
    _running = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

# ---------------------------------------------------------------------------
# Metric collection
# ---------------------------------------------------------------------------

# keep previous network counters for delta calculation
_prev_net: Optional[Any] = None
_prev_disk_io: Optional[Any] = None


def collect_metrics() -> Dict[str, Any]:
    """Return a dict of current system metrics."""
    global _prev_net, _prev_disk_io

    now = datetime.now(timezone.utc).isoformat()

    # CPU ------------------------------------------------------------------
    cpu_percent = psutil.cpu_percent(interval=0.5)  # short blocking sample
    cpu_freq = psutil.cpu_freq()

    # Memory ---------------------------------------------------------------
    mem = psutil.virtual_memory()

    # Disk usage -----------------------------------------------------------
    disk = psutil.disk_usage(os.environ.get("DISK_PATH", "C:\\" if sys.platform == "win32" else "/"))

    # Disk I/O (delta since last collection) — ransomware indicator --------
    disk_io = psutil.disk_io_counters()
    disk_read_bytes_delta = 0
    disk_write_bytes_delta = 0
    disk_read_count_delta = 0
    disk_write_count_delta = 0
    if disk_io:
        if _prev_disk_io is not None:
            disk_read_bytes_delta = disk_io.read_bytes - _prev_disk_io.read_bytes
            disk_write_bytes_delta = disk_io.write_bytes - _prev_disk_io.write_bytes
            disk_read_count_delta = disk_io.read_count - _prev_disk_io.read_count
            disk_write_count_delta = disk_io.write_count - _prev_disk_io.write_count
        _prev_disk_io = disk_io

    # Network I/O (delta) --------------------------------------------------
    net = psutil.net_io_counters()
    net_sent_delta = 0
    net_recv_delta = 0
    if _prev_net is not None:
        net_sent_delta = net.bytes_sent - _prev_net.bytes_sent
        net_recv_delta = net.bytes_recv - _prev_net.bytes_recv
    _prev_net = net

    return {
        "agent_id": AGENT_ID,
        "timestamp": now,
        # CPU
        "cpu_percent": round(cpu_percent, 2),
        "cpu_freq_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
        # Memory
        "memory_percent": round(mem.percent, 2),
        "memory_used_bytes": mem.used,
        "memory_total_bytes": mem.total,
        # Disk
        "disk_percent": round(disk.percent, 2),
        "disk_used_bytes": disk.used,
        "disk_total_bytes": disk.total,
        # Disk I/O deltas (high write entropy → ransomware indicator)
        "disk_read_bytes_delta": disk_read_bytes_delta,
        "disk_write_bytes_delta": disk_write_bytes_delta,
        "disk_read_count_delta": disk_read_count_delta,
        "disk_write_count_delta": disk_write_count_delta,
        # Network deltas
        "network_sent_bytes_delta": net_sent_delta,
        "network_recv_bytes_delta": net_recv_delta,
        "network_sent_bytes_total": net.bytes_sent,
        "network_recv_bytes_total": net.bytes_recv,
    }


# ---------------------------------------------------------------------------
# Sender with retry
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds (doubles each retry)


def send_metrics(payload: Dict[str, Any]) -> bool:
    """POST payload to the server.  Returns True on success."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": USER_API_KEY,
    }

    backoff = RETRY_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                INGEST_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                return True
            log.warning(
                "Server returned %s on attempt %d: %s",
                resp.status_code,
                attempt,
                resp.text[:200],
            )
        except requests.ConnectionError:
            log.warning(
                "Connection failed (attempt %d/%d). Retrying in %ds…",
                attempt,
                MAX_RETRIES,
                backoff,
            )
        except requests.Timeout:
            log.warning(
                "Request timed out (attempt %d/%d). Retrying in %ds…",
                attempt,
                MAX_RETRIES,
                backoff,
            )
        except requests.RequestException as exc:
            log.error("Unexpected request error: %s", exc)
            return False

        time.sleep(backoff)
        backoff *= 2

    log.error("Failed to send metrics after %d attempts.", MAX_RETRIES)
    return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    if not USER_API_KEY:
        log.error("USER_API_KEY is not set.  Please configure your .env file.")
        sys.exit(1)

    log.info("=" * 60)
    log.info("  System Monitoring Agent")
    log.info("  Agent ID    : %s", AGENT_ID)
    log.info("  Server URL  : %s", SERVER_URL)
    log.info("  Interval    : %d s", COLLECTION_INTERVAL)
    log.info("=" * 60)

    # Initial metric collection to prime deltas
    collect_metrics()
    log.info("Primed metric deltas.  Starting collection loop…")

    while _running:
        payload = collect_metrics()
        ok = send_metrics(payload)
        if ok:
            log.info(
                "Sent — CPU %.1f%% | MEM %.1f%% | DISK %.1f%% | DiskIO-W %s B",
                payload["cpu_percent"],
                payload["memory_percent"],
                payload["disk_percent"],
                payload["disk_write_bytes_delta"],
            )
        time.sleep(COLLECTION_INTERVAL)

    log.info("Agent stopped.")


if __name__ == "__main__":
    main()
