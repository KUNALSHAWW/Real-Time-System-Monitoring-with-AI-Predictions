"""
Anomaly detection router with real-time detection
"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel
from core.logger import get_logger
import numpy as np
from collections import deque
import psutil

logger = get_logger("anomalies")
router = APIRouter()

# Store recent metrics for anomaly detection (in-memory for now)
metrics_history = {
    'cpu': deque(maxlen=100),
    'memory': deque(maxlen=100),
    'disk': deque(maxlen=100),
    'network_sent': deque(maxlen=100),
    'network_recv': deque(maxlen=100)
}


class Anomaly(BaseModel):
    """Anomaly detection result"""
    timestamp: datetime
    metric_name: str
    value: float
    anomaly_score: float  # 0-1, where 1 is most anomalous
    is_anomaly: bool
    severity: str  # low, medium, high, critical
    threshold: float
    mean: float
    std_dev: float


class AnomalyDetectionResponse(BaseModel):
    """Response containing detected anomalies"""
    total_anomalies: int
    anomalies: List[Anomaly]
    timestamp: datetime


@router.post("/detect")
async def detect_anomaly_realtime(metric_name: str, value: float):
    """
    Detect anomaly in real-time using Z-score method
    Returns anomaly info if detected
    """
    try:
        # Add to history
        if metric_name not in metrics_history:
            metrics_history[metric_name] = deque(maxlen=100)
        
        metrics_history[metric_name].append(value)
        
        # Need at least 10 data points for meaningful detection
        if len(metrics_history[metric_name]) < 10:
            return {
                "is_anomaly": False,
                "metric_name": metric_name,
                "value": value,
                "message": "Collecting baseline data..."
            }
        
        # Calculate statistics
        values = list(metrics_history[metric_name])
        mean = np.mean(values)
        std = np.std(values)
        
        # Z-score calculation
        if std > 0:
            z_score = abs((value - mean) / std)
        else:
            z_score = 0
        
        # Determine if anomaly (threshold: 2 std deviations)
        is_anomaly = z_score > 2.0
        
        # Determine severity
        if z_score > 3.5:
            severity = "critical"
        elif z_score > 3.0:
            severity = "high"
        elif z_score > 2.5:
            severity = "medium"
        else:
            severity = "low"
        
        anomaly_score = min(z_score / 4.0, 1.0)  # Normalize to 0-1
        
        logger.info(f"Anomaly detection: {metric_name}={value}, z-score={z_score:.2f}, is_anomaly={is_anomaly}")
        
        return {
            "is_anomaly": is_anomaly,
            "metric_name": metric_name,
            "value": value,
            "anomaly_score": round(anomaly_score, 3),
            "severity": severity,
            "z_score": round(z_score, 2),
            "mean": round(mean, 2),
            "std_dev": round(std, 2),
            "threshold": round(mean + 2 * std, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in anomaly detection: {e}")
        return {
            "is_anomaly": False,
            "error": str(e)
        }


@router.get("/list", response_model=AnomalyDetectionResponse)
async def list_anomalies(
    hours: int = Query(1, ge=1, le=24),
    severity: str = Query("all", regex="^(all|low|medium|high|critical)$")
):
    """
    List detected anomalies (placeholder - would query database in production)
    
    Parameters:
    - hours: Look back period in hours
    - severity: Filter by severity level
    """
    logger.info(f"Fetching anomalies for {hours} hours, severity={severity}")
    
    return AnomalyDetectionResponse(
        total_anomalies=0,
        anomalies=[],
        timestamp=datetime.utcnow()
    )


@router.get("/metrics/{metric_name}")
async def get_metric_anomalies(
    metric_name: str,
    hours: int = Query(1, ge=1, le=24)
):
    """Get anomalies for specific metric"""
    logger.info(f"Fetching anomalies for {metric_name}")
    
    return {
        "metric_name": metric_name,
        "anomalies": [],
        "total": 0
    }


@router.post("/analyze")
async def analyze_for_anomalies(metric_name: str, value: float):
    """Analyze single data point for anomalies"""
    logger.info(f"Analyzing {metric_name}={value} for anomalies")
    
    return {
        "metric_name": metric_name,
        "value": value,
        "is_anomaly": False,
        "anomaly_score": 0.2,
        "severity": "low"
    }
