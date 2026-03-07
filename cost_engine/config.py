"""
Cost Engine Configuration

All settings are read from environment variables with sensible defaults.
No external API calls — all pricing is local mock data.
"""

import os

# Feature flag
COST_ENGINE_ENABLED: bool = os.getenv("COST_ENGINE_ENABLED", "true").lower() == "true"

# Default cloud provider for pricing
DEFAULT_PROVIDER: str = os.getenv("COST_DEFAULT_PROVIDER", "aws")

# Currency
CURRENCY: str = os.getenv("COST_CURRENCY", "USD")

# Monthly budget alert threshold (in CURRENCY)
MONTHLY_BUDGET_ALERT: float = float(os.getenv("COST_MONTHLY_BUDGET_ALERT", "1000.0"))

# Cost estimation granularity (hours to project)
PROJECTION_HOURS: int = int(os.getenv("COST_PROJECTION_HOURS", "720"))  # 30 days

# Panic button: savings threshold percentage to flag
PANIC_SAVINGS_THRESHOLD: float = float(os.getenv("COST_PANIC_SAVINGS_THRESHOLD", "20.0"))
