"""
Cost Calculator

Computes estimated cloud costs from system metrics and provides
panic-button analysis for cost reduction opportunities.

Uses mock pricing data from pricing_client.py — no external API calls.
"""

from typing import Any, Dict, List, Optional

from . import config
from . import pricing_client


def estimate_current_cost(
    instance_type: str,
    provider: str = None,
    hours: int = None,
) -> Dict[str, Any]:
    """
    Estimate cost for running an instance type for N hours.

    Returns dict with hourly, daily, monthly costs.
    """
    provider = provider or config.DEFAULT_PROVIDER
    hours = hours or config.PROJECTION_HOURS
    hourly = pricing_client.get_hourly_cost(instance_type, provider)

    if hourly is None:
        return {
            "error": f"Unknown instance type: {instance_type} (provider: {provider})",
            "instance_type": instance_type,
            "provider": provider,
        }

    return {
        "instance_type": instance_type,
        "provider": provider,
        "currency": config.CURRENCY,
        "hourly_cost": hourly,
        "daily_cost": round(hourly * 24, 2),
        "monthly_cost": round(hourly * hours, 2),
        "projection_hours": hours,
        "budget_alert": (hourly * hours) > config.MONTHLY_BUDGET_ALERT,
        "budget_limit": config.MONTHLY_BUDGET_ALERT,
    }


def estimate_fleet_cost(
    instances: List[Dict[str, Any]],
    provider: str = None,
) -> Dict[str, Any]:
    """
    Estimate total cost for a fleet of instances.

    Each instance dict should have:
    - instance_type: str
    - count: int (default 1)
    - provider: str (optional, falls back to default)

    Returns aggregated cost breakdown.
    """
    provider = provider or config.DEFAULT_PROVIDER
    total_hourly = 0.0
    breakdown = []

    for inst in instances:
        itype = inst["instance_type"]
        count = inst.get("count", 1)
        iprov = inst.get("provider", provider)
        hourly = pricing_client.get_hourly_cost(itype, iprov)

        if hourly is None:
            breakdown.append({
                "instance_type": itype,
                "count": count,
                "provider": iprov,
                "error": "unknown instance type",
            })
            continue

        line_hourly = hourly * count
        total_hourly += line_hourly
        breakdown.append({
            "instance_type": itype,
            "count": count,
            "provider": iprov,
            "hourly_per_unit": hourly,
            "hourly_total": round(line_hourly, 4),
            "monthly_total": round(line_hourly * config.PROJECTION_HOURS, 2),
        })

    total_monthly = round(total_hourly * config.PROJECTION_HOURS, 2)

    return {
        "currency": config.CURRENCY,
        "total_hourly": round(total_hourly, 4),
        "total_daily": round(total_hourly * 24, 2),
        "total_monthly": total_monthly,
        "budget_alert": total_monthly > config.MONTHLY_BUDGET_ALERT,
        "budget_limit": config.MONTHLY_BUDGET_ALERT,
        "breakdown": breakdown,
    }


def panic_button(
    instances: List[Dict[str, Any]],
    provider: str = None,
) -> Dict[str, Any]:
    """
    Panic Button — Find immediate cost reduction opportunities.

    Each instance dict should have:
    - instance_type: str
    - cpu_percent: float (actual average CPU usage)
    - memory_percent: float (actual average memory usage)
    - provider: str (optional)

    Returns list of recommendations with projected savings.
    """
    provider = provider or config.DEFAULT_PROVIDER
    recommendations = []
    total_savings_monthly = 0.0
    total_current_monthly = 0.0

    for inst in instances:
        itype = inst["instance_type"]
        cpu = inst.get("cpu_percent", 100.0)
        mem = inst.get("memory_percent", 100.0)
        iprov = inst.get("provider", provider)

        current_hourly = pricing_client.get_hourly_cost(itype, iprov)
        if current_hourly is None:
            continue

        current_monthly = current_hourly * config.PROJECTION_HOURS
        total_current_monthly += current_monthly

        alt = pricing_client.find_cheaper_alternative(itype, iprov, cpu, mem)

        if alt and alt["savings_percent"] >= config.PANIC_SAVINGS_THRESHOLD:
            total_savings_monthly += alt["savings_monthly"]
            recommendations.append({
                "current_instance": itype,
                "recommended_instance": alt["recommended"],
                "current_monthly": round(current_monthly, 2),
                "recommended_monthly": round(
                    alt["recommended_hourly"] * config.PROJECTION_HOURS, 2
                ),
                "savings_monthly": alt["savings_monthly"],
                "savings_percent": alt["savings_percent"],
                "reason": f"CPU at {cpu}%, Memory at {mem}% — instance oversized",
            })

    return {
        "currency": config.CURRENCY,
        "total_current_monthly": round(total_current_monthly, 2),
        "total_potential_savings_monthly": round(total_savings_monthly, 2),
        "savings_percent": round(
            (total_savings_monthly / total_current_monthly * 100)
            if total_current_monthly > 0 else 0, 1
        ),
        "recommendations_count": len(recommendations),
        "recommendations": recommendations,
    }
