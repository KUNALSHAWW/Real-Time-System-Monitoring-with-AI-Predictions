"""
Tests for the self-healing module.

Validates:
- MemoryLeakDetector correctly identifies growth trends
- AuditLogger writes events to file
- ContainerManager respects dry-run and cooldown
- Config defaults are safe (dry_run=True, enabled=false)
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add agent directory to path so we can import self_healing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))

from self_healing import config
from self_healing.audit_logger import log_event
from self_healing.memory_leak_detector import MemoryLeakDetector, ProcessMemoryTracker
from self_healing.container_manager import restart_container


# ---------------------------------------------------------------------------
# Config safety tests
# ---------------------------------------------------------------------------

class TestConfigDefaults:
    """Verify that config defaults are safe."""

    def test_auto_remediation_disabled_by_default(self):
        assert config.AUTO_REMEDIATION_ENABLED is False

    def test_dry_run_enabled_by_default(self):
        assert config.REMEDIATION_DRY_RUN is True

    def test_cooldown_is_positive(self):
        assert config.DEFAULT_COOLDOWN_SECONDS > 0

    def test_rate_limit_is_positive(self):
        assert config.MAX_REMEDIATIONS_PER_HOUR > 0

    def test_protected_processes_not_empty(self):
        assert len(config.PROTECTED_PROCESSES) > 0

    def test_leak_threshold_reasonable(self):
        # At least 100KB/min to avoid noise
        assert config.LEAK_THRESHOLD_BYTES_PER_MIN >= 100_000


# ---------------------------------------------------------------------------
# ProcessMemoryTracker tests
# ---------------------------------------------------------------------------

class TestProcessMemoryTracker:
    """Test RSS tracking and growth rate computation."""

    def test_add_sample(self):
        tracker = ProcessMemoryTracker(pid=1, name="test")
        tracker.add_sample(100_000_000)
        assert len(tracker.samples) == 1

    def test_max_samples_enforced(self):
        tracker = ProcessMemoryTracker(pid=1, name="test", max_samples=5)
        for i in range(10):
            tracker.add_sample(i * 1_000_000)
        assert len(tracker.samples) == 5

    def test_growth_rate_returns_none_insufficient_samples(self):
        tracker = ProcessMemoryTracker(pid=1, name="test")
        tracker.add_sample(100_000_000)
        assert tracker.compute_growth_rate() is None

    def test_growth_rate_detects_linear_growth(self):
        """Simulate a process growing at ~2 MB/min."""
        tracker = ProcessMemoryTracker(pid=1, name="leaky")
        base_rss = 500_000_000  # 500 MB
        growth_per_sec = 2_000_000 / 60  # 2 MB/min

        now = time.time()
        for i in range(20):  # 20 samples over 10 minutes
            t = now - (19 - i) * 30  # 30s intervals
            rss = int(base_rss + growth_per_sec * (i * 30))
            tracker.samples.append((t, rss))

        rate = tracker.compute_growth_rate(window_minutes=10)
        assert rate is not None
        # Should be approximately 2 MB/min (within 20% tolerance)
        assert abs(rate - 2_000_000) / 2_000_000 < 0.2

    def test_stable_process_no_growth(self):
        """Stable process should have near-zero growth rate."""
        tracker = ProcessMemoryTracker(pid=1, name="stable")
        now = time.time()
        for i in range(10):
            t = now - (9 - i) * 30
            tracker.samples.append((t, 200_000_000))  # constant RSS

        rate = tracker.compute_growth_rate(window_minutes=10)
        assert rate is not None
        assert abs(rate) < 10_000  # essentially zero


# ---------------------------------------------------------------------------
# MemoryLeakDetector tests
# ---------------------------------------------------------------------------

class TestMemoryLeakDetector:
    """Test the detector's process scanning and candidate detection."""

    def test_init_defaults(self):
        detector = MemoryLeakDetector()
        assert detector.threshold == config.LEAK_THRESHOLD_BYTES_PER_MIN
        assert detector.consecutive_windows == config.LEAK_CONSECUTIVE_WINDOWS

    @patch("self_healing.memory_leak_detector.psutil.process_iter")
    def test_sample_skips_protected_processes(self, mock_iter):
        """Protected processes should not be flagged."""
        mock_proc = MagicMock()
        mock_proc.info = {
            "pid": 1,
            "name": "systemd",  # protected
            "memory_info": MagicMock(rss=1_000_000_000),
        }
        mock_iter.return_value = [mock_proc]

        detector = MemoryLeakDetector()
        candidates = detector.sample_all_processes()

        assert len(candidates) == 0
        assert 1 not in detector.trackers

    @patch("self_healing.memory_leak_detector.psutil.process_iter")
    def test_sample_skips_small_processes(self, mock_iter):
        """Processes below min_rss_bytes should be ignored."""
        mock_proc = MagicMock()
        mock_proc.info = {
            "pid": 42,
            "name": "tiny_app",
            "memory_info": MagicMock(rss=1_000),  # 1 KB
        }
        mock_iter.return_value = [mock_proc]

        detector = MemoryLeakDetector(min_rss_bytes=50_000_000)
        candidates = detector.sample_all_processes()

        assert len(candidates) == 0


# ---------------------------------------------------------------------------
# Audit Logger tests
# ---------------------------------------------------------------------------

class TestAuditLogger:
    """Test that audit events are written to JSON-lines files."""

    def test_log_event_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(config, "AUDIT_LOG_DIR", tmpdir):
                event = log_event(
                    event_type="test_event",
                    target_name="test_process",
                    target_pid=1234,
                    reason="unit test",
                    dry_run=True,
                    success=True,
                )

                # Verify event dict
                assert event["event_type"] == "test_event"
                assert event["dry_run"] is True
                assert event["target_pid"] == 1234

                # Verify file was created
                log_files = list(Path(tmpdir).glob("selfheal-*.jsonl"))
                assert len(log_files) == 1

                # Verify content is valid JSON
                with open(log_files[0]) as f:
                    line = f.readline()
                    parsed = json.loads(line)
                    assert parsed["event_type"] == "test_event"


# ---------------------------------------------------------------------------
# Container Manager tests
# ---------------------------------------------------------------------------

class TestContainerManager:
    """Test that container manager respects safety guardrails."""

    def test_restart_blocked_when_disabled(self):
        """When AUTO_REMEDIATION_ENABLED=false, restart should be dry-run."""
        with patch.object(config, "AUTO_REMEDIATION_ENABLED", False):
            success, msg = restart_container(
                container_id="test-container",
                reason="unit test",
                dry_run=False,
            )
            assert success is True
            assert "DRY-RUN" in msg
            assert "AUTO_REMEDIATION_ENABLED=false" in msg

    def test_restart_blocked_when_dry_run(self):
        """When dry_run=True, no actual restart should happen."""
        with patch.object(config, "AUTO_REMEDIATION_ENABLED", True):
            with patch.object(config, "REMEDIATION_DRY_RUN", True):
                success, msg = restart_container(
                    container_id="test-container",
                    reason="unit test",
                    dry_run=True,
                )
                assert success is True
                assert "DRY-RUN" in msg
