"""
Prometheus Metrics for Self-Healing Operations

Defines counters, gauges, and histograms that the agent exposes at /metrics.
If prometheus_client is not installed, metrics are no-ops (stub mode).
"""

try:
    from prometheus_client import Counter, Gauge, Histogram

    remediation_actions_total = Counter(
        "selfheal_remediation_actions_total",
        "Total remediation actions (including dry-run)",
        ["action_type", "dry_run", "success"],
    )

    process_kills_total = Counter(
        "selfheal_process_kills_total",
        "Total process kill actions",
        ["dry_run"],
    )

    container_restarts_total = Counter(
        "selfheal_container_restarts_total",
        "Total container restart actions",
        ["dry_run"],
    )

    memory_leak_suspects = Gauge(
        "selfheal_memory_leak_suspects",
        "Current number of suspected memory leaking processes",
    )

    rss_growth_rate = Histogram(
        "selfheal_rss_growth_rate_bytes_per_min",
        "RSS growth rate distribution in bytes/minute",
        buckets=[100_000, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000],
    )

    PROMETHEUS_AVAILABLE = True

except ImportError:
    # Stub mode — metrics are no-ops when prometheus_client is not installed

    class _NoOp:
        """Stub metric that accepts any call and does nothing."""
        def __getattr__(self, _):
            return self

        def __call__(self, *args, **kwargs):
            return self

    remediation_actions_total = _NoOp()
    process_kills_total = _NoOp()
    container_restarts_total = _NoOp()
    memory_leak_suspects = _NoOp()
    rss_growth_rate = _NoOp()
    PROMETHEUS_AVAILABLE = False
