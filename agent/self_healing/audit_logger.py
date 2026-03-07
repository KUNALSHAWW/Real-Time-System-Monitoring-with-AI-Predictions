"""
Audit Logger for Self-Healing Operations

Every remediation action (whether dry-run or live) is logged to a
persistent JSON-lines file for forensic review.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from . import config


def _ensure_log_dir() -> Path:
    """Create audit log directory if it doesn't exist."""
    log_dir = Path(config.AUDIT_LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def log_event(
    event_type: str,
    target_name: str,
    target_pid: Optional[int],
    reason: str,
    dry_run: bool,
    success: bool,
    rollback_available: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Write a single audit event to the JSON-lines log file.

    Returns the event dict for further processing (e.g. DB insert).
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "epoch": time.time(),
        "event_type": event_type,
        "target_name": target_name,
        "target_pid": target_pid,
        "reason": reason,
        "dry_run": dry_run,
        "success": success,
        "rollback_available": rollback_available,
        "metadata": metadata or {},
        "auto_remediation_enabled": config.AUTO_REMEDIATION_ENABLED,
    }

    try:
        log_dir = _ensure_log_dir()
        # One file per day for easy rotation
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = log_dir / f"selfheal-{date_str}.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except OSError:
        # If we can't write to log dir, fall back to stderr
        import sys
        print(f"[AUDIT] {json.dumps(event, default=str)}", file=sys.stderr)

    return event
