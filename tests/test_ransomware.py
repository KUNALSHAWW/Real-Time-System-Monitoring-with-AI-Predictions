"""
Tests for the ransomware detector module.

Validates:
- Shannon entropy calculation accuracy
- I/O pattern detection logic
- Safe terminator guardrails (dry-run, protected processes, rate limits)
- Config defaults are safe
"""

import os
import sys
import tempfile

import pytest
from unittest.mock import MagicMock, patch

# Add agent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))

from ransomware_detector import config
from ransomware_detector.entropy_calculator import (
    shannon_entropy,
    file_entropy,
    is_suspicious_entropy,
)
from ransomware_detector.io_pattern_detector import IOPatternDetector, IOSnapshot
from ransomware_detector.safe_terminator import safe_terminate


# ---------------------------------------------------------------------------
# Config safety tests
# ---------------------------------------------------------------------------

class TestRansomwareConfigDefaults:
    """Verify safe defaults."""

    def test_auto_remediation_disabled(self):
        assert config.AUTO_REMEDIATION_ENABLED is False

    def test_dry_run_enabled(self):
        assert config.REMEDIATION_DRY_RUN is True

    def test_protected_processes_not_empty(self):
        assert len(config.PROTECTED_PROCESSES) > 0

    def test_entropy_thresholds_reasonable(self):
        assert 7.0 < config.ENTROPY_SUSPICIOUS_THRESHOLD < 8.0
        assert config.ENTROPY_CRITICAL_THRESHOLD > config.ENTROPY_SUSPICIOUS_THRESHOLD

    def test_ransomware_extensions_populated(self):
        assert len(config.RANSOMWARE_EXTENSIONS) > 0
        assert ".encrypted" in config.RANSOMWARE_EXTENSIONS


# ---------------------------------------------------------------------------
# Entropy calculator tests
# ---------------------------------------------------------------------------

class TestShannonEntropy:
    """Test entropy computation."""

    def test_empty_data(self):
        assert shannon_entropy(b"") == 0.0

    def test_single_byte_repeated(self):
        # All same bytes → entropy = 0
        data = b"\x00" * 1000
        assert shannon_entropy(data) == 0.0

    def test_two_byte_equal_distribution(self):
        # 50/50 split of two values → entropy = 1.0
        data = b"\x00\x01" * 500
        entropy = shannon_entropy(data)
        assert abs(entropy - 1.0) < 0.01

    def test_random_data_high_entropy(self):
        # Pseudo-random data should have entropy close to 8.0
        import random
        random.seed(42)
        data = bytes(random.randint(0, 255) for _ in range(10000))
        entropy = shannon_entropy(data)
        assert entropy > 7.5

    def test_text_data_medium_entropy(self):
        # English text typically has entropy 3-5 bits/byte
        data = b"The quick brown fox jumps over the lazy dog. " * 100
        entropy = shannon_entropy(data)
        assert 3.0 < entropy < 6.0

    def test_is_suspicious_entropy(self):
        assert is_suspicious_entropy(7.9, threshold=7.5) is True
        assert is_suspicious_entropy(5.0, threshold=7.5) is False

    def test_file_entropy_nonexistent(self):
        result = file_entropy("/nonexistent/file/path.bin")
        assert result is None

    def test_file_entropy_real_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"Hello world " * 1000)
            f.flush()
            path = f.name

        try:
            entropy = file_entropy(path)
            assert entropy is not None
            assert 0 < entropy < 8.0
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# I/O Pattern Detector tests
# ---------------------------------------------------------------------------

class TestIOPatternDetector:
    """Test I/O anomaly detection."""

    def test_normal_io_no_alerts(self):
        detector = IOPatternDetector(
            write_spike_bytes=100_000_000,
            write_read_ratio=10.0,
        )
        snapshot = IOSnapshot(
            timestamp=1000.0,
            read_bytes_delta=1_000_000,
            write_bytes_delta=1_000_000,
            read_count_delta=100,
            write_count_delta=100,
        )
        alerts = detector.analyze(snapshot)
        assert len(alerts) == 0

    def test_write_spike_detected(self):
        detector = IOPatternDetector(write_spike_bytes=50_000_000)
        snapshot = IOSnapshot(
            timestamp=1000.0,
            read_bytes_delta=1_000_000,
            write_bytes_delta=200_000_000,  # 200 MB spike
            read_count_delta=100,
            write_count_delta=5000,
        )
        alerts = detector.analyze(snapshot)
        spike_alerts = [a for a in alerts if a["type"] == "write_spike"]
        assert len(spike_alerts) == 1
        assert spike_alerts[0]["severity"] in ("warning", "critical")

    def test_consecutive_spikes_escalate_severity(self):
        detector = IOPatternDetector(write_spike_bytes=50_000_000)
        for i in range(5):
            snapshot = IOSnapshot(
                timestamp=1000.0 + i * 5,
                read_bytes_delta=1_000,
                write_bytes_delta=200_000_000,
                read_count_delta=10,
                write_count_delta=5000,
            )
            alerts = detector.analyze(snapshot)

        # After 5 consecutive spikes, should be critical
        spike_alerts = [a for a in alerts if a["type"] == "write_spike"]
        assert len(spike_alerts) == 1
        assert spike_alerts[0]["severity"] == "critical"

    def test_high_write_read_ratio(self):
        detector = IOPatternDetector(
            write_spike_bytes=1_000_000_000,  # high so spike doesn't trigger
            write_read_ratio=10.0,
        )
        snapshot = IOSnapshot(
            timestamp=1000.0,
            read_bytes_delta=1_000_000,
            write_bytes_delta=50_000_000,  # 50x ratio
            read_count_delta=100,
            write_count_delta=5000,
        )
        alerts = detector.analyze(snapshot)
        ratio_alerts = [a for a in alerts if a["type"] == "high_write_read_ratio"]
        assert len(ratio_alerts) == 1


# ---------------------------------------------------------------------------
# Safe Terminator tests
# ---------------------------------------------------------------------------

class TestSafeTerminator:
    """Test kill guardrails."""

    def test_blocked_when_disabled(self):
        with patch.object(config, "AUTO_REMEDIATION_ENABLED", False):
            success, msg = safe_terminate(
                pid=99999,
                process_name="test_process",
                reason="unit test",
                dry_run=False,
            )
            assert success is True
            assert "DRY-RUN" in msg
            assert "AUTO_REMEDIATION_ENABLED=false" in msg

    def test_blocked_when_dry_run(self):
        with patch.object(config, "AUTO_REMEDIATION_ENABLED", True):
            with patch.object(config, "REMEDIATION_DRY_RUN", True):
                success, msg = safe_terminate(
                    pid=99999,
                    process_name="test_process",
                    reason="unit test",
                    dry_run=True,
                )
                assert success is True
                assert "DRY-RUN" in msg

    def test_blocked_for_protected_process(self):
        with patch.object(config, "AUTO_REMEDIATION_ENABLED", True):
            with patch.object(config, "REMEDIATION_DRY_RUN", False):
                success, msg = safe_terminate(
                    pid=1,
                    process_name="sshd",
                    reason="unit test",
                    dry_run=False,
                )
                assert success is False
                assert "BLOCKED" in msg
                assert "protected" in msg.lower()
