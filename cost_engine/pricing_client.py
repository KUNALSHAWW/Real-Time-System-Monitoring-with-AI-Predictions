"""
Mock Pricing Client

Provides cloud instance pricing data without any external API calls.
All data is hardcoded for MVP — production version would query
AWS Pricing API, Azure Retail Prices API, or GCP Cloud Billing.

Instance types are mapped to hourly costs in USD.
"""

from typing import Dict, List, Optional

from . import config


# ---------------------------------------------------------------------------
# Mock pricing data (representative as of 2024)
# ---------------------------------------------------------------------------

_AWS_PRICING: Dict[str, Dict] = {
    "t3.micro": {"vcpu": 2, "memory_gb": 1, "hourly_usd": 0.0104},
    "t3.small": {"vcpu": 2, "memory_gb": 2, "hourly_usd": 0.0208},
    "t3.medium": {"vcpu": 2, "memory_gb": 4, "hourly_usd": 0.0416},
    "t3.large": {"vcpu": 2, "memory_gb": 8, "hourly_usd": 0.0832},
    "t3.xlarge": {"vcpu": 4, "memory_gb": 16, "hourly_usd": 0.1664},
    "t3.2xlarge": {"vcpu": 8, "memory_gb": 32, "hourly_usd": 0.3328},
    "m5.large": {"vcpu": 2, "memory_gb": 8, "hourly_usd": 0.096},
    "m5.xlarge": {"vcpu": 4, "memory_gb": 16, "hourly_usd": 0.192},
    "m5.2xlarge": {"vcpu": 8, "memory_gb": 32, "hourly_usd": 0.384},
    "m5.4xlarge": {"vcpu": 16, "memory_gb": 64, "hourly_usd": 0.768},
    "c5.large": {"vcpu": 2, "memory_gb": 4, "hourly_usd": 0.085},
    "c5.xlarge": {"vcpu": 4, "memory_gb": 8, "hourly_usd": 0.170},
    "c5.2xlarge": {"vcpu": 8, "memory_gb": 16, "hourly_usd": 0.340},
    "r5.large": {"vcpu": 2, "memory_gb": 16, "hourly_usd": 0.126},
    "r5.xlarge": {"vcpu": 4, "memory_gb": 32, "hourly_usd": 0.252},
}

_AZURE_PRICING: Dict[str, Dict] = {
    "B1s": {"vcpu": 1, "memory_gb": 1, "hourly_usd": 0.0104},
    "B2s": {"vcpu": 2, "memory_gb": 4, "hourly_usd": 0.0416},
    "D2s_v3": {"vcpu": 2, "memory_gb": 8, "hourly_usd": 0.096},
    "D4s_v3": {"vcpu": 4, "memory_gb": 16, "hourly_usd": 0.192},
    "D8s_v3": {"vcpu": 8, "memory_gb": 32, "hourly_usd": 0.384},
    "E2s_v3": {"vcpu": 2, "memory_gb": 16, "hourly_usd": 0.126},
    "F2s_v2": {"vcpu": 2, "memory_gb": 4, "hourly_usd": 0.085},
}

_GCP_PRICING: Dict[str, Dict] = {
    "e2-micro": {"vcpu": 0.25, "memory_gb": 1, "hourly_usd": 0.0084},
    "e2-small": {"vcpu": 0.5, "memory_gb": 2, "hourly_usd": 0.0168},
    "e2-medium": {"vcpu": 1, "memory_gb": 4, "hourly_usd": 0.0336},
    "n1-standard-1": {"vcpu": 1, "memory_gb": 3.75, "hourly_usd": 0.0475},
    "n1-standard-2": {"vcpu": 2, "memory_gb": 7.5, "hourly_usd": 0.0950},
    "n1-standard-4": {"vcpu": 4, "memory_gb": 15, "hourly_usd": 0.1900},
    "n1-standard-8": {"vcpu": 8, "memory_gb": 30, "hourly_usd": 0.3800},
}

_PRICING_DB = {
    "aws": _AWS_PRICING,
    "azure": _AZURE_PRICING,
    "gcp": _GCP_PRICING,
}


def get_providers() -> List[str]:
    """Return list of supported cloud providers."""
    return list(_PRICING_DB.keys())


def get_instance_types(provider: str = None) -> Dict[str, Dict]:
    """Return all instance types and pricing for a provider."""
    provider = provider or config.DEFAULT_PROVIDER
    return _PRICING_DB.get(provider.lower(), {})


def get_hourly_cost(instance_type: str, provider: str = None) -> Optional[float]:
    """
    Get the hourly cost for a specific instance type.
    Returns None if instance type not found.
    """
    provider = provider or config.DEFAULT_PROVIDER
    instances = _PRICING_DB.get(provider.lower(), {})
    instance = instances.get(instance_type)
    return instance["hourly_usd"] if instance else None


def find_best_fit(
    vcpu_needed: float,
    memory_gb_needed: float,
    provider: str = None,
) -> Optional[Dict]:
    """
    Find the cheapest instance that meets the CPU and memory requirements.
    Returns dict with instance_type, specs, and hourly cost.
    """
    provider = provider or config.DEFAULT_PROVIDER
    instances = _PRICING_DB.get(provider.lower(), {})

    candidates = []
    for name, specs in instances.items():
        if specs["vcpu"] >= vcpu_needed and specs["memory_gb"] >= memory_gb_needed:
            candidates.append({"instance_type": name, **specs})

    if not candidates:
        return None

    # Sort by hourly cost, return cheapest
    candidates.sort(key=lambda x: x["hourly_usd"])
    return candidates[0]


def find_cheaper_alternative(
    current_instance: str,
    provider: str = None,
    actual_cpu_percent: float = 100.0,
    actual_memory_percent: float = 100.0,
) -> Optional[Dict]:
    """
    Given current instance and actual utilization, suggest a cheaper alternative.

    If actual CPU usage is < 50% and memory < 50%, the instance is likely
    oversized and a smaller one could work.
    """
    provider = provider or config.DEFAULT_PROVIDER
    instances = _PRICING_DB.get(provider.lower(), {})
    current = instances.get(current_instance)

    if current is None:
        return None

    # Estimate actual needs (with 30% headroom)
    needed_vcpu = current["vcpu"] * (actual_cpu_percent / 100) * 1.3
    needed_memory = current["memory_gb"] * (actual_memory_percent / 100) * 1.3

    best = find_best_fit(needed_vcpu, needed_memory, provider)

    if best and best["hourly_usd"] < current["hourly_usd"]:
        savings_hourly = current["hourly_usd"] - best["hourly_usd"]
        savings_monthly = savings_hourly * config.PROJECTION_HOURS
        return {
            "current": current_instance,
            "recommended": best["instance_type"],
            "current_hourly": current["hourly_usd"],
            "recommended_hourly": best["hourly_usd"],
            "savings_hourly": round(savings_hourly, 4),
            "savings_monthly": round(savings_monthly, 2),
            "savings_percent": round(
                (savings_hourly / current["hourly_usd"]) * 100, 1
            ),
        }

    return None
