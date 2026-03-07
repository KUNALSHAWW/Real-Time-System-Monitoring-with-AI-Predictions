"""
Memory Leak Detection Heuristic

Monitors RSS (Resident Set Size) of processes over time and flags
those with sustained growth patterns.

Threshold Math:
- Sample RSS every 30 seconds
- Compute linear regression over 10-minute window (20 samples)
- If slope > 1 MB/minute for 3 consecutive windows, flag as leak
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import psutil
import numpy as np

from . import config


@dataclass
class ProcessMemoryTracker:
    """Track RSS history for a single process."""
    pid: int
    name: str
    samples: List[Tuple[float, int]] = field(default_factory=list)
    max_samples: int = 60  # 30 min at 30s intervals

    def add_sample(self, rss_bytes: int) -> None:
        now = time.time()
        self.samples.append((now, rss_bytes))
        if len(self.samples) > self.max_samples:
            self.samples.pop(0)

    def compute_growth_rate(self, window_minutes: int = 10) -> Optional[float]:
        """
        Compute RSS growth rate in bytes/minute over the last N minutes.
        Returns None if insufficient samples.
        """
        if len(self.samples) < 4:
            return None

        cutoff = time.time() - (window_minutes * 60)
        recent = [(t, rss) for t, rss in self.samples if t >= cutoff]

        if len(recent) < 4:
            return None

        times = np.array([t for t, _ in recent])
        rss_values = np.array([rss for _, rss in recent])

        # Linear regression: rss = slope * time + intercept
        coeffs = np.polyfit(times, rss_values, 1)
        slope_bytes_per_sec = coeffs[0]
        slope_bytes_per_min = slope_bytes_per_sec * 60

        return slope_bytes_per_min


class MemoryLeakDetector:
    """
    Detect memory leaks by tracking RSS trends across processes.

    Thresholds (configurable via env):
    - LEAK_THRESHOLD_BYTES_PER_MIN: Growth rate to flag (default 1 MB/min)
    - LEAK_CONSECUTIVE_WINDOWS: Consecutive anomalous windows (default 3)
    - LEAK_MIN_RSS_BYTES: Ignore processes below this RSS (default 50 MB)
    """

    def __init__(
        self,
        threshold_bytes_per_min: float = None,
        consecutive_windows: int = None,
        min_rss_bytes: int = None,
    ):
        self.threshold = threshold_bytes_per_min or config.LEAK_THRESHOLD_BYTES_PER_MIN
        self.consecutive_windows = consecutive_windows or config.LEAK_CONSECUTIVE_WINDOWS
        self.min_rss_bytes = min_rss_bytes or config.LEAK_MIN_RSS_BYTES
        self.trackers: Dict[int, ProcessMemoryTracker] = {}
        self.anomaly_counts: Dict[int, int] = defaultdict(int)
        self._last_pids: set = set()

    def sample_all_processes(self) -> List[dict]:
        """
        Sample RSS for all running processes and update trackers.
        Returns list of potential leak candidates.
        """
        current_pids = set()
        candidates = []

        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                info = proc.info
                pid = info["pid"]
                name = info["name"] or "unknown"
                mem = info.get("memory_info")

                if mem is None:
                    continue

                rss = mem.rss
                current_pids.add(pid)

                if rss < self.min_rss_bytes:
                    continue

                if name.lower() in config.PROTECTED_PROCESSES:
                    continue

                if pid not in self.trackers:
                    self.trackers[pid] = ProcessMemoryTracker(pid=pid, name=name)

                tracker = self.trackers[pid]
                tracker.add_sample(rss)

                growth_rate = tracker.compute_growth_rate(window_minutes=10)

                if growth_rate is not None and growth_rate > self.threshold:
                    self.anomaly_counts[pid] += 1

                    if self.anomaly_counts[pid] >= self.consecutive_windows:
                        candidates.append({
                            "pid": pid,
                            "name": name,
                            "current_rss_mb": rss / 1_000_000,
                            "growth_rate_mb_per_min": growth_rate / 1_000_000,
                            "consecutive_anomalies": self.anomaly_counts[pid],
                            "recommendation": (
                                "RESTART" if self.anomaly_counts[pid] >= 5 else "MONITOR"
                            ),
                        })
                else:
                    self.anomaly_counts[pid] = 0

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Clean up trackers for dead processes
        dead_pids = self._last_pids - current_pids
        for pid in dead_pids:
            self.trackers.pop(pid, None)
            self.anomaly_counts.pop(pid, None)

        self._last_pids = current_pids
        return candidates


if __name__ == "__main__":
    detector = MemoryLeakDetector()
    print("MemoryLeakDetector initialized.")
    print(f"  Threshold: {detector.threshold / 1e6:.1f} MB/min growth")
    print(f"  Consecutive windows: {detector.consecutive_windows}")
    print(f"  Min RSS filter: {detector.min_rss_bytes / 1e6:.0f} MB")
    print(f"  Protected processes: {len(config.PROTECTED_PROCESSES)}")
    print("\nSampling processes once...")
    candidates = detector.sample_all_processes()
    print(f"  Processes tracked: {len(detector.trackers)}")
    print(f"  Candidates (need {detector.consecutive_windows}+ anomalies): {len(candidates)}")
    print("\nDry-run complete. No actions taken.")
