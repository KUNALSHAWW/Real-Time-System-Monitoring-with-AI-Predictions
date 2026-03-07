"""
I/O Pattern Detector

Monitors disk I/O patterns for ransomware-like behaviour:
- Sudden write spikes (bulk encryption in progress)
- High write-to-read ratio (reading files → encrypting → writing)
- Sustained high I/O (persistent encryption campaign)

Works with delta values from sensor.py's collect_metrics().
"""

from dataclasses import dataclass, field
from typing import List, Optional

from . import config


@dataclass
class IOSnapshot:
    """A single I/O measurement snapshot."""
    timestamp: float
    read_bytes_delta: int
    write_bytes_delta: int
    read_count_delta: int
    write_count_delta: int


class IOPatternDetector:
    """
    Detect ransomware-like I/O patterns from metric deltas.

    Tracks recent I/O snapshots and flags anomalies based on:
    1. Write spike: single interval write_bytes_delta > threshold
    2. Write/read ratio: write >> read suggests encrypt-in-place
    3. Sustained high writes: multiple consecutive intervals
    """

    def __init__(
        self,
        write_spike_bytes: int = None,
        write_read_ratio: float = None,
        history_size: int = 20,
    ):
        self.write_spike_bytes = write_spike_bytes or config.IO_WRITE_SPIKE_BYTES
        self.write_read_ratio = write_read_ratio or config.IO_WRITE_READ_RATIO_THRESHOLD
        self.history: List[IOSnapshot] = []
        self.history_size = history_size
        self._consecutive_spikes = 0

    def add_snapshot(self, snapshot: IOSnapshot) -> None:
        """Add an I/O snapshot and maintain history window."""
        self.history.append(snapshot)
        if len(self.history) > self.history_size:
            self.history.pop(0)

    def check_write_spike(self) -> Optional[dict]:
        """
        Check the latest snapshot for a write spike.
        Returns alert dict or None.
        """
        if not self.history:
            return None

        latest = self.history[-1]

        if latest.write_bytes_delta > self.write_spike_bytes:
            self._consecutive_spikes += 1
            return {
                "type": "write_spike",
                "write_bytes_delta": latest.write_bytes_delta,
                "threshold": self.write_spike_bytes,
                "consecutive_spikes": self._consecutive_spikes,
                "severity": "critical" if self._consecutive_spikes >= 3 else "warning",
            }
        else:
            self._consecutive_spikes = 0
            return None

    def check_write_read_ratio(self) -> Optional[dict]:
        """
        Check if write/read ratio is suspiciously high.
        Returns alert dict or None.
        """
        if not self.history:
            return None

        latest = self.history[-1]
        read = max(latest.read_bytes_delta, 1)  # avoid division by zero
        ratio = latest.write_bytes_delta / read

        if ratio > self.write_read_ratio and latest.write_bytes_delta > 1_000_000:
            return {
                "type": "high_write_read_ratio",
                "ratio": round(ratio, 2),
                "threshold": self.write_read_ratio,
                "write_bytes": latest.write_bytes_delta,
                "read_bytes": latest.read_bytes_delta,
                "severity": "warning",
            }
        return None

    def analyze(self, snapshot: IOSnapshot) -> List[dict]:
        """
        Add a snapshot and run all pattern checks.
        Returns list of alert dicts (may be empty).
        """
        self.add_snapshot(snapshot)
        alerts = []

        spike = self.check_write_spike()
        if spike:
            alerts.append(spike)

        ratio = self.check_write_read_ratio()
        if ratio:
            alerts.append(ratio)

        return alerts
