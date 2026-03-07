"""
Prometheus Metrics for Ransomware Detection

Counters and gauges for ransomware detection events.
Falls back to no-op stubs if prometheus_client is not installed.
"""

try:
    from prometheus_client import Counter, Gauge, Histogram

    ransomware_alerts_total = Counter(
        "ransom_alerts_total",
        "Total ransomware alerts raised",
        ["alert_type", "severity"],
    )

    ransomware_kills_total = Counter(
        "ransom_kills_total",
        "Total process kill actions for ransomware",
        ["dry_run"],
    )

    entropy_scans_total = Counter(
        "ransom_entropy_scans_total",
        "Total file entropy scans performed",
    )

    high_entropy_files = Gauge(
        "ransom_high_entropy_files",
        "Current count of files with suspicious entropy",
    )

    io_write_spike_events = Counter(
        "ransom_io_write_spike_events_total",
        "Total I/O write spike events detected",
    )

    PROMETHEUS_AVAILABLE = True

except ImportError:

    class _NoOp:
        def __getattr__(self, _):
            return self
        def __call__(self, *args, **kwargs):
            return self

    ransomware_alerts_total = _NoOp()
    ransomware_kills_total = _NoOp()
    entropy_scans_total = _NoOp()
    high_entropy_files = _NoOp()
    io_write_spike_events = _NoOp()
    PROMETHEUS_AVAILABLE = False
