"""
System metrics router - Data collection and retrieval
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from core.logger import get_logger
import psutil

logger = get_logger("metrics")
router = APIRouter()


class MetricDataPoint(BaseModel):
    """Single metric data point"""
    timestamp: datetime
    value: float
    unit: str
    host: str


class MetricsResponse(BaseModel):
    """Metrics response"""
    metric_name: str
    data_points: List[MetricDataPoint]
    timestamp: datetime


@router.get("/cpu", response_model=MetricsResponse)
async def get_cpu_metrics(
    hours: int = Query(1, ge=1, le=24),
    host: Optional[str] = None
):
    """
    Get CPU utilization metrics
    
    Parameters:
    - hours: Number of hours of historical data (1-24)
    - host: Optional specific host to query
    """
    logger.info(f"Fetching CPU metrics for {hours} hours")
    
    return MetricsResponse(
        metric_name="cpu_utilization",
        data_points=[],
        timestamp=datetime.utcnow()
    )


@router.get("/memory", response_model=MetricsResponse)
async def get_memory_metrics(
    hours: int = Query(1, ge=1, le=24),
    host: Optional[str] = None
):
    """Get memory utilization metrics"""
    logger.info(f"Fetching memory metrics for {hours} hours")
    
    return MetricsResponse(
        metric_name="memory_utilization",
        data_points=[],
        timestamp=datetime.utcnow()
    )


@router.get("/disk", response_model=MetricsResponse)
async def get_disk_metrics(
    hours: int = Query(1, ge=1, le=24),
    host: Optional[str] = None
):
    """Get disk utilization metrics"""
    logger.info(f"Fetching disk metrics for {hours} hours")
    
    return MetricsResponse(
        metric_name="disk_utilization",
        data_points=[],
        timestamp=datetime.utcnow()
    )


@router.get("/network", response_model=MetricsResponse)
async def get_network_metrics(
    hours: int = Query(1, ge=1, le=24),
    host: Optional[str] = None
):
    """Get network metrics"""
    logger.info(f"Fetching network metrics for {hours} hours")
    
    return MetricsResponse(
        metric_name="network_throughput",
        data_points=[],
        timestamp=datetime.utcnow()
    )


@router.post("/custom")
async def post_custom_metrics(metric_name: str, value: float):
    """Post custom metrics"""
    logger.info(f"Custom metric received: {metric_name}={value}")
    
    return {
        "status": "received",
        "metric_name": metric_name,
        "value": value
    }


@router.get("/current")
async def get_current_metrics():
    """
    Get current real-time system metrics
    Returns current CPU, memory, disk, and network metrics
    """
    try:
        # Collect real-time metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "disk_percent": round(disk.percent, 2),
            "network_sent": network.bytes_sent,
            "network_recv": network.bytes_recv,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "disk_total": disk.total,
            "disk_used": disk.used
        }
    except Exception as e:
        logger.error(f"Error fetching current metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")
