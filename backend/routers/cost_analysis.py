"""
Cost Analysis API Router

Endpoints:
  POST /api/v1/cost/estimate  — Estimate costs for a set of instances
  POST /api/v1/cost/panic     — Panic button: find savings opportunities
  GET  /api/v1/cost/providers  — List supported providers
  GET  /api/v1/cost/instances  — List instance types and pricing

No external API calls — all pricing is from local mock data.
"""

import sys
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to path so cost_engine can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cost_engine import config as cost_config
from cost_engine.pricing_client import (
    get_providers,
    get_instance_types,
    find_best_fit,
)
from cost_engine.cost_calculator import (
    estimate_current_cost,
    estimate_fleet_cost,
    panic_button,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class InstanceEstimateRequest(BaseModel):
    instance_type: str = Field(..., description="Cloud instance type (e.g. t3.large)")
    provider: Optional[str] = Field(None, description="Cloud provider (aws, azure, gcp)")
    hours: Optional[int] = Field(None, description="Hours to project cost for")


class FleetInstance(BaseModel):
    instance_type: str
    count: int = 1
    provider: Optional[str] = None


class FleetEstimateRequest(BaseModel):
    instances: List[FleetInstance]
    provider: Optional[str] = None


class PanicInstance(BaseModel):
    instance_type: str
    cpu_percent: float = Field(100.0, ge=0, le=100, description="Average CPU usage %")
    memory_percent: float = Field(100.0, ge=0, le=100, description="Average memory usage %")
    provider: Optional[str] = None


class PanicRequest(BaseModel):
    instances: List[PanicInstance]
    provider: Optional[str] = None


class RightSizeRequest(BaseModel):
    vcpu_needed: float = Field(..., gt=0, description="Required vCPUs")
    memory_gb_needed: float = Field(..., gt=0, description="Required memory in GB")
    provider: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/providers")
async def list_providers():
    """List all supported cloud providers."""
    return {"providers": get_providers()}


@router.get("/instances")
async def list_instances(provider: Optional[str] = None):
    """List all instance types and pricing for a provider."""
    provider = provider or cost_config.DEFAULT_PROVIDER
    instances = get_instance_types(provider)
    if not instances:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    return {
        "provider": provider,
        "currency": cost_config.CURRENCY,
        "instance_count": len(instances),
        "instances": instances,
    }


@router.post("/estimate")
async def estimate_cost(req: InstanceEstimateRequest):
    """Estimate cost for a single instance type."""
    result = estimate_current_cost(
        instance_type=req.instance_type,
        provider=req.provider,
        hours=req.hours,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/estimate/fleet")
async def estimate_fleet(req: FleetEstimateRequest):
    """Estimate total cost for a fleet of instances."""
    instances = [inst.model_dump() for inst in req.instances]
    return estimate_fleet_cost(instances, req.provider)


@router.post("/panic")
async def cost_panic(req: PanicRequest):
    """
    Panic Button — find immediate cost reduction opportunities.

    Send current instance types with their actual CPU/memory utilization.
    Returns downsizing recommendations with projected monthly savings.
    """
    instances = [inst.model_dump() for inst in req.instances]
    return panic_button(instances, req.provider)


@router.post("/rightsize")
async def right_size(req: RightSizeRequest):
    """
    Find the cheapest instance that meets given vCPU and memory requirements.
    """
    result = find_best_fit(
        vcpu_needed=req.vcpu_needed,
        memory_gb_needed=req.memory_gb_needed,
        provider=req.provider,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No instance found meeting {req.vcpu_needed} vCPU / {req.memory_gb_needed} GB memory",
        )
    return {
        "provider": req.provider or cost_config.DEFAULT_PROVIDER,
        "currency": cost_config.CURRENCY,
        "recommendation": result,
        "monthly_cost": round(result["hourly_usd"] * cost_config.PROJECTION_HOURS, 2),
    }
