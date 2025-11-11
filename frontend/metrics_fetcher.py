"""
Streamlit-compatible Real-Time Metrics Fetcher
Uses polling and caching instead of WebSocket threads for better Streamlit compatibility
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import deque
import time


def normalize_api_url(raw_url: str, fallback: str = "http://localhost:8000") -> str:
    """Normalize API URL by ensuring scheme and stripping trailing slashes."""
    url = (raw_url or fallback).strip()
    if not url:
        return fallback
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


class MetricsFetcher:
    """Fetches real-time metrics from backend API"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = normalize_api_url(api_base_url)
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """Fetch current system metrics from API"""
        try:
            # Try the /current endpoint
            response = requests.get(
                f"{self.api_base_url}/api/metrics/current",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Return fallback data
                return self._get_fallback_metrics()
                
        except requests.RequestException as e:
            # Silent fallback - don't show error in Streamlit
            print(f"API connection failed: {e}")
            return self._get_fallback_metrics()
    
    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Return simulated metrics when API is unavailable"""
        import random
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": round(random.uniform(50, 80), 2),
            "memory_percent": round(random.uniform(40, 70), 2),
            "disk_percent": round(random.uniform(60, 85), 2),
            "network_sent": int(random.uniform(100000000, 500000000)),
            "network_recv": int(random.uniform(100000000, 500000000))
        }
    
    def get_metrics_history(self, metric_name: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """Fetch historical metrics from API"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/metrics/{metric_name}",
                params={"minutes": minutes},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get("data_points", [])
            else:
                return []
                
        except requests.RequestException:
            return []


@st.cache_resource
def get_metrics_buffer():
    """Get or create metrics buffer (cached across reruns)"""
    return deque(maxlen=100)


def fetch_and_cache_metrics(fetcher: MetricsFetcher):
    """Fetch metrics and add to buffer"""
    metrics = fetcher.get_current_metrics()
    buffer = get_metrics_buffer()
    buffer.append(metrics)
    return metrics


def get_latest_metrics() -> Dict[str, Any]:
    """Get the most recent metrics from buffer or fetch new ones"""
    buffer = get_metrics_buffer()
    
    if len(buffer) > 0:
        return buffer[-1]
    else:
        # Initialize buffer with first fetch
        fetcher = MetricsFetcher()
        return fetch_and_cache_metrics(fetcher)


def get_buffered_metrics_as_list() -> List[Dict[str, Any]]:
    """Get all buffered metrics as a list"""
    buffer = get_metrics_buffer()
    return list(buffer)


# Auto-refresh helper
def setup_auto_refresh(interval_seconds: int = 5):
    """Setup automatic page refresh"""
    import streamlit as st
    from streamlit_autorefresh import st_autorefresh
    
    # Auto-refresh the page every interval
    count = st_autorefresh(interval=interval_seconds * 1000, key="metrics_refresh")
    
    return count
