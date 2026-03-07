"""
Container Manager — Docker restart wrapper with safety guardrails.

Wraps Docker CLI to restart leaking containers with:
- Cooldown enforcement (default 300s between restarts)
- Rate limiting (max N restarts/hour)
- Dry-run default (no actual restart unless explicitly enabled)
- Pre-restart log collection
- Audit trail for every operation

IMPORTANT: This module defaults to dry_run=True and requires
AUTO_REMEDIATION_ENABLED=true to perform actual restarts.
"""

import json
import subprocess
import time
from typing import Dict, Optional, Tuple

from . import config
from .audit_logger import log_event


# Track last restart time per container for cooldown
_last_restart: Dict[str, float] = {}
# Track total restarts this hour for rate limiting
_hourly_restarts: list = []


def _check_cooldown(container_id: str) -> bool:
    """Return True if the container has cooled down since last restart."""
    last = _last_restart.get(container_id, 0)
    elapsed = time.time() - last
    return elapsed >= config.DEFAULT_COOLDOWN_SECONDS


def _check_rate_limit() -> bool:
    """Return True if under the hourly restart limit."""
    now = time.time()
    one_hour_ago = now - 3600
    # Prune old entries
    _hourly_restarts[:] = [t for t in _hourly_restarts if t > one_hour_ago]
    return len(_hourly_restarts) < config.MAX_REMEDIATIONS_PER_HOUR


def collect_logs(container_id: str, tail: int = 100) -> str:
    """
    Collect recent container logs before restart for forensic analysis.
    Returns log output as string, or error message.
    """
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"[log collection failed: {e}]"


def restart_container(
    container_id: str,
    reason: str,
    dry_run: bool = True,
) -> Tuple[bool, str]:
    """
    Restart a Docker container with full safety checks.

    Safety guardrails:
    1. AUTO_REMEDIATION_ENABLED must be true
    2. dry_run must be explicitly set to False
    3. Container must have passed cooldown period
    4. Hourly rate limit must not be exceeded
    5. Logs are collected before restart
    6. Every action is audit-logged

    Returns (success: bool, message: str).

    Undo plan: `docker start <container_id>` if restart fails.
    """
    # Guard 1: Feature flag
    if not config.AUTO_REMEDIATION_ENABLED:
        msg = f"[DRY-RUN] Would restart container {container_id}: {reason} (AUTO_REMEDIATION_ENABLED=false)"
        log_event(
            event_type="container_restart",
            target_name=container_id,
            target_pid=None,
            reason=reason,
            dry_run=True,
            success=True,
            rollback_available=True,
            metadata={"blocked_by": "feature_flag"},
        )
        return True, msg

    # Guard 2: Explicit dry_run
    if dry_run or config.REMEDIATION_DRY_RUN:
        msg = f"[DRY-RUN] Would restart container {container_id}: {reason}"
        log_event(
            event_type="container_restart",
            target_name=container_id,
            target_pid=None,
            reason=reason,
            dry_run=True,
            success=True,
            rollback_available=True,
            metadata={"blocked_by": "dry_run"},
        )
        return True, msg

    # Guard 3: Cooldown
    if not _check_cooldown(container_id):
        msg = f"[COOLDOWN] Skipping restart of {container_id}: cooldown active"
        log_event(
            event_type="container_restart",
            target_name=container_id,
            target_pid=None,
            reason=reason,
            dry_run=False,
            success=False,
            metadata={"blocked_by": "cooldown"},
        )
        return False, msg

    # Guard 4: Rate limit
    if not _check_rate_limit():
        msg = f"[RATE-LIMIT] Skipping restart of {container_id}: hourly limit reached"
        log_event(
            event_type="container_restart",
            target_name=container_id,
            target_pid=None,
            reason=reason,
            dry_run=False,
            success=False,
            metadata={"blocked_by": "rate_limit"},
        )
        return False, msg

    # Collect logs before restart
    pre_restart_logs = collect_logs(container_id)

    # Perform restart
    try:
        result = subprocess.run(
            ["docker", "restart", container_id],
            capture_output=True,
            text=True,
            timeout=60,
        )
        success = result.returncode == 0
        msg = result.stdout.strip() if success else result.stderr.strip()

        _last_restart[container_id] = time.time()
        _hourly_restarts.append(time.time())

        log_event(
            event_type="container_restart",
            target_name=container_id,
            target_pid=None,
            reason=reason,
            dry_run=False,
            success=success,
            rollback_available=True,
            metadata={
                "return_code": result.returncode,
                "pre_restart_log_lines": len(pre_restart_logs.splitlines()),
            },
        )
        return success, msg

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        msg = f"[ERROR] Docker restart failed: {e}"
        log_event(
            event_type="container_restart",
            target_name=container_id,
            target_pid=None,
            reason=reason,
            dry_run=False,
            success=False,
            metadata={"error": str(e)},
        )
        return False, msg
