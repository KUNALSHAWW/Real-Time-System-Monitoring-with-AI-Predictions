"""
Process Investigator

Examines running processes for ransomware indicators:
- Processes with open file handles to many files
- Processes creating files with known ransomware extensions
- Processes with suspicious names

Uses psutil to inspect process attributes without requiring
elevated privileges (may miss some data on Windows/macOS).
"""

import os
from typing import Dict, List

import psutil

from . import config


def find_suspicious_by_name() -> List[Dict]:
    """
    Scan running processes for names matching known ransomware patterns.
    Returns list of suspicious process dicts.
    """
    suspects = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            info = proc.info
            name = (info.get("name") or "").lower()
            pid = info["pid"]

            # Skip protected processes
            if name in config.PROTECTED_PROCESSES:
                continue

            # Check against known suspicious names
            for pattern in config.SUSPICIOUS_PROCESS_NAMES:
                if pattern in name:
                    suspects.append({
                        "pid": pid,
                        "name": info["name"],
                        "match_type": "name_pattern",
                        "pattern": pattern,
                        "cmdline": " ".join(info.get("cmdline") or [])[:200],
                    })
                    break

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return suspects


def check_open_files_for_ransomware_extensions(
    pid: int,
) -> List[Dict]:
    """
    Check if a specific process has open files with ransomware extensions.
    Returns list of suspicious file dicts.
    """
    suspicious_files = []

    try:
        proc = psutil.Process(pid)
        open_files = proc.open_files()

        for f in open_files:
            ext = os.path.splitext(f.path)[1].lower()
            if ext in config.RANSOMWARE_EXTENSIONS:
                suspicious_files.append({
                    "pid": pid,
                    "path": f.path,
                    "extension": ext,
                    "match_type": "ransomware_extension",
                })

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    return suspicious_files


def investigate_process(pid: int) -> Dict:
    """
    Gather detailed information about a suspicious process.
    Returns dict with process details for audit logging.
    """
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            info = {
                "pid": pid,
                "name": proc.name(),
                "exe": proc.exe(),
                "cmdline": " ".join(proc.cmdline())[:500],
                "status": proc.status(),
                "create_time": proc.create_time(),
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_rss_bytes": proc.memory_info().rss,
                "num_threads": proc.num_threads(),
                "username": proc.username(),
            }

            # Try to get open file count (may fail on some OS)
            try:
                info["open_files_count"] = len(proc.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                info["open_files_count"] = -1

            return info

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        return {
            "pid": pid,
            "error": str(e),
        }
