"""
Safe Terminator — Process kill with full safety guardrails.

Terminates suspicious processes ONLY when ALL safety checks pass:
1. AUTO_REMEDIATION_ENABLED must be true
2. dry_run must be explicitly False
3. Process must NOT be in the protected list
4. Cooldown must have elapsed since last kill
5. Rate limit must not be exceeded
6. Every action is audit-logged (even dry-runs)

Undo plan: Killing a process is not directly reversible.
The audit log records all details for forensic analysis.
Container-level restart is the recovery path.

IMPORTANT: This module defaults to dry_run=True. No process is
ever killed unless explicitly enabled via environment variables.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

import psutil

from . import config


# Track kill history for cooldown and rate limiting
_last_kill: Dict[int, float] = {}  # pid -> timestamp
_hourly_kills: list = []


def _audit_log(event: dict) -> None:
    """Write audit event to JSON-lines file."""
    try:
        log_dir = Path(config.AUDIT_LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = log_dir / f"ransom-{date_str}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except OSError:
        import sys
        print(f"[RANSOM-AUDIT] {json.dumps(event, default=str)}", file=sys.stderr)


def _check_cooldown(pid: int) -> bool:
    """Return True if cooldown has elapsed for this PID."""
    last = _last_kill.get(pid, 0)
    return (time.time() - last) >= config.DEFAULT_COOLDOWN_SECONDS


def _check_rate_limit() -> bool:
    """Return True if under the hourly kill limit."""
    now = time.time()
    one_hour_ago = now - 3600
    _hourly_kills[:] = [t for t in _hourly_kills if t > one_hour_ago]
    return len(_hourly_kills) < config.MAX_KILLS_PER_HOUR


def safe_terminate(
    pid: int,
    process_name: str,
    reason: str,
    evidence: Optional[Dict] = None,
    dry_run: bool = True,
) -> Tuple[bool, str]:
    """
    Safely terminate a process with full guardrail checks.

    Safety chain:
    1. Feature flag check (AUTO_REMEDIATION_ENABLED)
    2. Dry-run check
    3. Protected process whitelist
    4. Cooldown check
    5. Rate limit check
    6. Audit log (always, even on dry-run)

    Returns (success: bool, message: str).
    """
    audit_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "process_terminate",
        "target_name": process_name,
        "target_pid": pid,
        "reason": reason,
        "evidence": evidence or {},
        "auto_remediation_enabled": config.AUTO_REMEDIATION_ENABLED,
    }

    # Guard 1: Feature flag
    if not config.AUTO_REMEDIATION_ENABLED:
        msg = f"[DRY-RUN] Would terminate PID {pid} ({process_name}): {reason} (AUTO_REMEDIATION_ENABLED=false)"
        audit_event.update({"dry_run": True, "success": True, "blocked_by": "feature_flag"})
        _audit_log(audit_event)
        return True, msg

    # Guard 2: Dry-run
    if dry_run or config.REMEDIATION_DRY_RUN:
        msg = f"[DRY-RUN] Would terminate PID {pid} ({process_name}): {reason}"
        audit_event.update({"dry_run": True, "success": True, "blocked_by": "dry_run"})
        _audit_log(audit_event)
        return True, msg

    # Guard 3: Protected process whitelist
    if process_name.lower() in config.PROTECTED_PROCESSES:
        msg = f"[BLOCKED] Cannot terminate protected process: {process_name} (PID {pid})"
        audit_event.update({"dry_run": False, "success": False, "blocked_by": "protected_process"})
        _audit_log(audit_event)
        return False, msg

    # Guard 4: Cooldown
    if not _check_cooldown(pid):
        msg = f"[COOLDOWN] Skipping terminate of PID {pid}: cooldown active"
        audit_event.update({"dry_run": False, "success": False, "blocked_by": "cooldown"})
        _audit_log(audit_event)
        return False, msg

    # Guard 5: Rate limit
    if not _check_rate_limit():
        msg = f"[RATE-LIMIT] Skipping terminate of PID {pid}: hourly limit reached"
        audit_event.update({"dry_run": False, "success": False, "blocked_by": "rate_limit"})
        _audit_log(audit_event)
        return False, msg

    # Execute termination
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # SIGTERM — allows graceful shutdown
        proc.wait(timeout=5)
        msg = f"[TERMINATED] PID {pid} ({process_name}): {reason}"
        _last_kill[pid] = time.time()
        _hourly_kills.append(time.time())
        audit_event.update({"dry_run": False, "success": True})
        _audit_log(audit_event)
        return True, msg

    except psutil.NoSuchProcess:
        msg = f"[GONE] PID {pid} already terminated"
        audit_event.update({"dry_run": False, "success": True, "note": "already_dead"})
        _audit_log(audit_event)
        return True, msg

    except psutil.AccessDenied:
        msg = f"[DENIED] Insufficient privileges to terminate PID {pid}"
        audit_event.update({"dry_run": False, "success": False, "error": "access_denied"})
        _audit_log(audit_event)
        return False, msg

    except psutil.TimeoutExpired:
        # Process didn't terminate gracefully, but we don't force-kill
        msg = f"[TIMEOUT] PID {pid} did not terminate within 5s (SIGTERM sent, not escalated to SIGKILL)"
        audit_event.update({"dry_run": False, "success": False, "error": "timeout"})
        _audit_log(audit_event)
        return False, msg
