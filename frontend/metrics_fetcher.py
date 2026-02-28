"""
Streamlit-compatible Real-Time Metrics Fetcher
Production-ready with proper error handling for Hugging Face Spaces deployment
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
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


class ConnectionError(Exception):
    """Custom exception for connection errors"""
    pass


class MetricsFetcher:
    """Fetches real-time metrics from backend API with proper error handling"""
    
    def __init__(self, api_base_url: str = None):
        # Use environment variable if not provided
        default_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.api_base_url = normalize_api_url(api_base_url or default_url)
        self.last_error: Optional[str] = None
        self.is_connected: bool = False
        
    def check_connection(self) -> bool:
        """Check if backend is accessible"""
        try:
            response = requests.get(
                f"{self.api_base_url}/health",
                timeout=5
            )
            self.is_connected = response.status_code == 200
            if self.is_connected:
                self.last_error = None
            return self.is_connected
        except requests.exceptions.ConnectionError:
            self.is_connected = False
            self.last_error = "CONNECTION_ERROR: Cannot reach backend server"
            return False
        except requests.exceptions.Timeout:
            self.is_connected = False
            self.last_error = "TIMEOUT_ERROR: Backend server not responding"
            return False
        except Exception as e:
            self.is_connected = False
            self.last_error = f"UNKNOWN_ERROR: {str(e)}"
            return False
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Fetch current system metrics from API.
        Raises ConnectionError if backend is unreachable.
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/api/metrics/current",
                timeout=10
            )
            
            if response.status_code == 200:
                self.is_connected = True
                self.last_error = None
                return response.json()
            else:
                self.is_connected = False
                self.last_error = f"API_ERROR: Status {response.status_code}"
                raise ConnectionError(f"API returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            self.is_connected = False
            self.last_error = "CONNECTION_ERROR: Cannot reach backend server"
            raise ConnectionError(self.last_error) from e
            
        except requests.exceptions.Timeout as e:
            self.is_connected = False
            self.last_error = "TIMEOUT_ERROR: Backend server not responding"
            raise ConnectionError(self.last_error) from e
            
        except requests.exceptions.RequestException as e:
            self.is_connected = False
            self.last_error = f"REQUEST_ERROR: {str(e)}"
            raise ConnectionError(self.last_error) from e
    
    def get_metrics_history(self, metric_name: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """Fetch historical metrics from API"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/metrics/history",
                params={"minutes": minutes},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("data_points", [])
            else:
                return []
                
        except requests.RequestException:
            return []
    
    def get_error_message(self) -> Optional[str]:
        """Get the last error message"""
        return self.last_error
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.is_connected,
            "api_url": self.api_base_url,
            "error": self.last_error,
            "timestamp": datetime.now().isoformat()
        }


@st.cache_resource
def get_metrics_buffer():
    """Get or create metrics buffer (cached across reruns)"""
    return deque(maxlen=100)


@st.cache_resource
def get_fetcher():
    """Get or create MetricsFetcher instance"""
    api_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    return MetricsFetcher(api_url)


def fetch_and_cache_metrics(fetcher: MetricsFetcher) -> Dict[str, Any]:
    """
    Fetch metrics and add to buffer.
    Raises ConnectionError if backend is unreachable.
    """
    metrics = fetcher.get_current_metrics()  # This will raise ConnectionError if failed
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
        fetcher = get_fetcher()
        return fetch_and_cache_metrics(fetcher)


def get_buffered_metrics_as_list() -> List[Dict[str, Any]]:
    """Get all buffered metrics as a list"""
    buffer = get_metrics_buffer()
    return list(buffer)


def get_connection_error_ui() -> None:
    """Display connection error UI in Streamlit"""
    fetcher = get_fetcher()
    
    st.error("⚠️ **Connection Error**")
    st.markdown(f"""
    Unable to connect to the backend server.
    
    **Backend URL:** `{fetcher.api_base_url}`
    
    **Error:** {fetcher.last_error or 'Unknown error'}
    
    **Possible Solutions:**
    1. Ensure the backend is running
    2. Check the `BACKEND_URL` environment variable
    3. Verify network connectivity
    4. Check if the backend Space is awake (Hugging Face Spaces may sleep)
    """)


# Auto-refresh helper
def setup_auto_refresh(interval_seconds: int = 5):
    """Setup automatic page refresh"""
    try:
        from streamlit_autorefresh import st_autorefresh
        # Auto-refresh the page every interval
        count = st_autorefresh(interval=interval_seconds * 1000, key="metrics_refresh")
        return count
    except ImportError:
        # Fallback if streamlit-autorefresh is not installed
        return None
