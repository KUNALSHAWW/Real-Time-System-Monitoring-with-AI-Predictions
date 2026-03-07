"""
Ransomware Detector Configuration

All settings are read from environment variables with safe defaults.
"""

import os

# Feature flags — both must be true for live termination
AUTO_REMEDIATION_ENABLED: bool = os.getenv("AUTO_REMEDIATION_ENABLED", "false").lower() == "true"
REMEDIATION_DRY_RUN: bool = os.getenv("REMEDIATION_DRY_RUN", "true").lower() == "true"

# --- Entropy thresholds ---
# Shannon entropy of encrypted data is typically 7.9-8.0 bits/byte.
# Normal binaries are 5-7, text files 3-5.
ENTROPY_SUSPICIOUS_THRESHOLD: float = float(os.getenv("ENTROPY_SUSPICIOUS_THRESHOLD", "7.5"))
ENTROPY_CRITICAL_THRESHOLD: float = float(os.getenv("ENTROPY_CRITICAL_THRESHOLD", "7.9"))

# --- I/O pattern thresholds ---
# Bytes written per collection interval that trigger suspicion (default 100 MB)
IO_WRITE_SPIKE_BYTES: int = int(os.getenv("IO_WRITE_SPIKE_BYTES", str(100_000_000)))
# Ratio of write_bytes to read_bytes that suggests encryption (write >> read)
IO_WRITE_READ_RATIO_THRESHOLD: float = float(os.getenv("IO_WRITE_READ_RATIO_THRESHOLD", "10.0"))

# --- Process investigation ---
# Known ransomware file extensions (for rename/create detection)
RANSOMWARE_EXTENSIONS: set = {
    ".encrypted", ".locked", ".crypto", ".crypt", ".enc",
    ".locky", ".cerber", ".zepto", ".zzzzz", ".micro",
    ".aaa", ".abc", ".xyz", ".zzz", ".odin",
    ".thor", ".osiris", ".sage", ".wallet",
}

# Suspicious process names (case-insensitive partial match)
SUSPICIOUS_PROCESS_NAMES: set = {
    "ransom", "crypt", "locker", "wanna", "petya",
}

# --- Safety ---
# Processes that must NEVER be killed
PROTECTED_PROCESSES: set = {
    "systemd", "init", "kernel", "sshd", "bash", "sh", "zsh",
    "explorer.exe", "services.exe", "lsass.exe", "csrss.exe",
    "wininit.exe", "winlogon.exe", "svchost.exe", "system",
    "smss.exe", "dwm.exe", "taskhostw.exe",
}

DEFAULT_COOLDOWN_SECONDS: int = int(os.getenv("REMEDIATION_COOLDOWN_SECONDS", "300"))
MAX_KILLS_PER_HOUR: int = int(os.getenv("MAX_KILLS_PER_HOUR", "5"))

# Audit log directory
AUDIT_LOG_DIR: str = os.getenv("AUDIT_LOG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "logs", "ransomware"))
