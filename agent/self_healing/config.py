"""
Self-Healing configuration — loaded from environment variables.

All destructive actions default to dry_run=True and require
AUTO_REMEDIATION_ENABLED=true to execute.
"""

import os

# Feature gate — must be explicitly enabled
AUTO_REMEDIATION_ENABLED: bool = (
    os.getenv("AUTO_REMEDIATION_ENABLED", "false").lower() == "true"
)
REMEDIATION_DRY_RUN: bool = (
    os.getenv("REMEDIATION_DRY_RUN", "true").lower() == "true"
)

# Environment — never auto-remediate outside production unless forced
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# Memory leak detection
LEAK_THRESHOLD_BYTES_PER_MIN: float = float(
    os.getenv("LEAK_THRESHOLD_BYTES_PER_MIN", "1000000")  # 1 MB/min
)
LEAK_CONSECUTIVE_WINDOWS: int = int(os.getenv("LEAK_CONSECUTIVE_WINDOWS", "3"))
LEAK_MIN_RSS_BYTES: int = int(os.getenv("LEAK_MIN_RSS_BYTES", "50000000"))  # 50 MB
LEAK_SAMPLE_INTERVAL: int = int(os.getenv("LEAK_SAMPLE_INTERVAL", "30"))  # seconds

# Cooldown
DEFAULT_COOLDOWN_SECONDS: int = int(os.getenv("REMEDIATION_COOLDOWN_SECONDS", "300"))

# Rate limit — max remediation actions per hour
MAX_REMEDIATIONS_PER_HOUR: int = int(os.getenv("MAX_REMEDIATIONS_PER_HOUR", "5"))

# Audit log directory
AUDIT_LOG_DIR: str = os.getenv("AUDIT_LOG_DIR", "/var/log/selfhealer")

# Operator approval webhook (stub — set URL to enable)
OPERATOR_APPROVAL_WEBHOOK: str = os.getenv("OPERATOR_APPROVAL_WEBHOOK", "")

# Protected processes — NEVER kill these
PROTECTED_PROCESSES = {
    "system", "systemd", "init", "kernel", "kthreadd",
    "ksoftirqd", "kworker", "migration", "watchdog",
    "rcu_sched", "rcu_bh", "cron", "sshd", "rsyslogd",
    "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "svchost.exe", "explorer.exe", "dwm.exe",
    "winlogon.exe", "taskmgr.exe", "spoolsv.exe",
    "launchd", "kernel_task", "WindowServer",
    "python", "python3", "python.exe", "sensor.py",
    "ransomware_detector", "self_healing",
}
