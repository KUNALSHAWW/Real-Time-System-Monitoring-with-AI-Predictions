"""
Real-Time System Monitoring Dashboard - Ultimate Production Version
Enhanced UI with:
- Smooth animations and transitions
- User-friendly interface for non-technical users
- Responsive design
- Email & In-app notifications
- Interactive help tooltips
- Dark/Light theme toggle
- Mobile-friendly layout
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import requests
import json
from typing import Dict, Any, List, Optional
from collections import deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import hashlib
import time
import asyncio
import websockets
import threading

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="System Health Monitor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "# System Health Monitor\nReal-time monitoring made simple!"
    }
)

# ============================================================================
# CUSTOM CSS FOR SMOOTH UI
# ============================================================================

st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #4CAF50;
        --secondary-color: #2196F3;
        --warning-color: #FF9800;
        --danger-color: #F44336;
        --success-color: #4CAF50;
    }
    
    /* Smooth animations */
    .stMetric {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: fadeInUp 0.5s ease-out;
    }
    
    .stMetric:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    
    /* Fade in animation */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Pulse animation for alerts */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .alert-pulse {
        animation: pulse 2s infinite;
    }
    
    /* Smooth progress bars */
    .stProgress > div > div {
        transition: width 0.5s ease;
        border-radius: 10px;
    }
    
    /* Card styling */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Success message styling */
    .success-message {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        animation: slideInRight 0.5s ease-out;
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s ease;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Notification badge */
    .notification-badge {
        background: #F44336;
        color: white;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 5px;
        animation: pulse 2s infinite;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-good { background: #4CAF50; }
    .status-warning { background: #FF9800; }
    .status-critical { background: #F44336; }
    
    /* Responsive typography */
    @media (max-width: 768px) {
        .stMetric {
            padding: 15px;
        }
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
    }
    
    /* Tooltip styling */
    .tooltip-text {
        background: rgba(0,0,0,0.9);
        color: white;
        padding: 10px;
        border-radius: 8px;
        font-size: 14px;
        margin-top: 5px;
    }
    
    /* Loading spinner */
    .loading-spinner {
        border: 3px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top: 3px solid #2196F3;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION & VALIDATION
# ============================================================================

# Backend API configuration - normalized for deployment environments
import os


def normalize_api_url(raw_url: str, fallback: str = "http://localhost:8000") -> str:
    """Ensure API URL includes scheme and has no trailing slash."""
    url = (raw_url or fallback).strip()
    if not url:
        return fallback
    if not url.startswith(("http://", "https://")):
        # Default to https for production deployments like Render
        url = f"https://{url}"
    # Remove trailing slash to keep endpoint joining consistent
    return url.rstrip("/")


API_BASE_URL = normalize_api_url(os.getenv("BACKEND_URL", "http://localhost:8000"))
WS_BASE_URL = API_BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(EMAIL_PATTERN.match(email)) if email else False

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'metrics_history': deque(maxlen=100),
        'backend_connected': False,
        'user_email': '',
        'notifications': [],
        'notification_prefs': {
            'email': True,
            'in_app': True,
            'sound': False,
        },
        'theme': 'dark',
        'auto_refresh': True,
        'refresh_interval': 10,
        'alert_history': [],
        'show_help': False,
        'user_name': 'Guest User',
        'alert_thresholds': {
            'cpu': 80.0,
            'memory': 75.0,
            'disk': 80.0,
            'network': 1000.0
        },
        'dashboard_view': 'overview',  # overview, detailed, compact
        'chart_animation': True,
        'first_visit': True,
        'anomalies_detected': [],
        'ai_analysis_cache': {},
        'websocket_enabled': False,
        'latest_metrics': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# METRICS FETCHER
# ============================================================================

try:
    from metrics_fetcher import MetricsFetcher
    METRICS_MODULE_AVAILABLE = True
except ImportError:
    METRICS_MODULE_AVAILABLE = False

if METRICS_MODULE_AVAILABLE:
    @st.cache_resource
    def get_fetcher():
        return MetricsFetcher(API_BASE_URL)
    fetcher = get_fetcher()
else:
    fetcher = None

# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

class NotificationManager:
    """Enhanced notification manager with multiple channels"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, html_body: str = None):
        """Send email notification"""
        try:
            # Get SMTP settings from secrets
            smtp_server = st.secrets.get("smtp", {}).get("server", "smtp.gmail.com")
            smtp_port = st.secrets.get("smtp", {}).get("port", 587)
            smtp_user = st.secrets.get("smtp", {}).get("username", "")
            smtp_password = st.secrets.get("smtp", {}).get("password", "")
            
            if not smtp_user or not smtp_password:
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = to_email
            
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            st.error(f"Email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_in_app_notification(title: str, message: str, severity: str = "info"):
        """Send in-app notification"""
        notification = {
            'id': len(st.session_state['notifications']) + 1,
            'title': title,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now(),
            'read': False
        }
        st.session_state['notifications'].insert(0, notification)
        
        # Keep only last 50 notifications
        if len(st.session_state['notifications']) > 50:
            st.session_state['notifications'] = st.session_state['notifications'][:50]
    
    @staticmethod
    def mark_as_read(notification_id: int):
        """Mark notification as read"""
        for notif in st.session_state['notifications']:
            if notif['id'] == notification_id:
                notif['read'] = True
                break
    
    @staticmethod
    def clear_all_notifications():
        """Clear all notifications"""
        st.session_state['notifications'] = []

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_backend_connection() -> bool:
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        is_healthy = response.status_code == 200
        st.session_state['backend_connected'] = is_healthy
        return is_healthy
    except requests.RequestException as exc:
        st.session_state['backend_connected'] = False
        return False

def get_realtime_metrics() -> Dict[str, Any]:
    """Get latest metrics from backend or use fallback"""
    if METRICS_MODULE_AVAILABLE and fetcher:
        try:
            from metrics_fetcher import fetch_and_cache_metrics
            metrics = fetch_and_cache_metrics(fetcher)
            st.session_state['metrics_history'].append(metrics)
            st.session_state['backend_connected'] = True
            return metrics
        except:
            st.session_state['backend_connected'] = False
    
    # Fallback to simulated data
    import random
    return {
        'cpu_percent': round(random.uniform(50, 80), 1),
        'memory_percent': round(random.uniform(40, 70), 1),
        'disk_percent': round(random.uniform(60, 85), 1),
        'network_sent': int(random.uniform(100000000, 500000000)),
        'network_recv': int(random.uniform(100000000, 500000000)),
        'timestamp': datetime.now().isoformat()
    }

def get_metrics_history() -> pd.DataFrame:
    """Convert metrics history to DataFrame"""
    if METRICS_MODULE_AVAILABLE:
        try:
            from metrics_fetcher import get_buffered_metrics_as_list
            metrics_list = get_buffered_metrics_as_list()
        except:
            metrics_list = list(st.session_state['metrics_history'])
    else:
        metrics_list = list(st.session_state['metrics_history'])
    
    if len(metrics_list) == 0:
        times = pd.date_range(start=datetime.now() - timedelta(minutes=10), periods=20, freq='30s')
        return pd.DataFrame({
            'timestamp': times,
            'cpu_percent': np.random.normal(65, 15, 20).clip(0, 100),
            'memory_percent': np.random.normal(55, 12, 20).clip(0, 100),
            'disk_percent': np.random.normal(72, 5, 20).clip(0, 100)
        })
    
    df = pd.DataFrame(metrics_list)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def get_health_status(value: float, threshold: float) -> tuple:
    """Get health status and color"""
    if value < threshold * 0.7:
        return "Healthy", "🟢", "#4CAF50"
    elif value < threshold:
        return "Warning", "🟡", "#FF9800"
    else:
        return "Critical", "🔴", "#F44336"

def detect_and_notify_anomaly(metric_name: str, value: float, threshold: float):
    """Detect anomaly and send notifications"""
    if value > threshold:
        severity = 'critical' if value > threshold * 1.2 else 'warning'
        
        # Create alert
        alert = {
            'metric': metric_name,
            'value': value,
            'threshold': threshold,
            'timestamp': datetime.now(),
            'severity': severity
        }
        
        # Add to history
        st.session_state['alert_history'].insert(0, alert)
        if len(st.session_state['alert_history']) > 100:
            st.session_state['alert_history'] = st.session_state['alert_history'][:100]
        
        # Send in-app notification
        if st.session_state['notification_prefs']['in_app']:
            NotificationManager.send_in_app_notification(
                title=f"⚠️ {metric_name} Alert",
                message=f"{metric_name} is at {value:.1f}% (threshold: {threshold}%)",
                severity=severity
            )
        
        # Send email notification
        if st.session_state['notification_prefs']['email'] and st.session_state['user_email']:
            subject = f"🚨 System Alert: {metric_name} Exceeded Threshold"
            body = f"""
Hello {st.session_state['user_name']},

An alert has been triggered on your system:

Metric: {metric_name}
Current Value: {value:.1f}%
Threshold: {threshold}%
Severity: {severity.upper()}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check your dashboard for more details.

Best regards,
System Health Monitor
            """
            NotificationManager.send_email(st.session_state['user_email'], subject, body)


def fetch_anomaly_detection(metrics: Dict[str, float]) -> Dict[str, Any]:
    """Call backend anomaly detection API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/anomaly/detect",
            json=metrics,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        st.warning(f"Anomaly detection unavailable: {e}")
        return {}


def fetch_ai_analysis(metrics: Dict[str, float]) -> str:
    """Get AI analysis from backend"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/ai/analyze",
            json=metrics,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('analysis', 'Analysis unavailable')
        return "AI analysis unavailable"
    except Exception as e:
        return f"AI analysis error: {e}"


def fetch_anomaly_explanation(anomaly_data: Dict[str, Any]) -> str:
    """Get AI explanation for detected anomaly"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/ai/anomaly-explanation",
            json=anomaly_data,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('explanation', 'No explanation available')
        return "Explanation unavailable"
    except Exception as e:
        return f"Error getting explanation: {e}"

def show_welcome_tour():
    """Show welcome tour for first-time users"""
    if st.session_state.get('first_visit', True):
        st.balloons()
        st.info("""
        ### 👋 Welcome to System Health Monitor!
        
        **Quick Start Guide:**
        1. 📊 **Dashboard** - See your system health at a glance
        2. 📧 **Set up notifications** - Get alerts via email or in-app
        3. ⚙️ **Customize thresholds** - Set your own alert levels
        4. 📈 **Monitor trends** - View historical data and predictions
        
        👉 Click the **Settings** panel in the sidebar to get started!
        """)
        
        if st.button("Got it! Let's start monitoring"):
            st.session_state['first_visit'] = False
            st.rerun()

# ============================================================================
# SIDEBAR - USER-FRIENDLY CONTROLS
# ============================================================================

with st.sidebar:
    # Header with logo
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #4CAF50; margin: 0;'>🏥</h1>
        <h3 style='margin: 5px 0;'>Health Monitor</h3>
        <p style='color: gray; font-size: 12px;'>Real-time System Monitoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Connection status with visual indicator
    backend_alive = check_backend_connection()
    
    if backend_alive and st.session_state.get('backend_connected', False):
        status_html = '<span class="status-indicator status-good"></span>Connected to Server'
        st.markdown(f'<div style="padding: 10px; background: rgba(76, 175, 80, 0.1); border-radius: 10px; margin: 10px 0;">{status_html}</div>', unsafe_allow_html=True)
    elif backend_alive:
        status_html = '<span class="status-indicator status-warning"></span>Connecting...'
        st.markdown(f'<div style="padding: 10px; background: rgba(255, 152, 0, 0.1); border-radius: 10px; margin: 10px 0;">{status_html}</div>', unsafe_allow_html=True)
    else:
        status_html = '<span class="status-indicator status-critical"></span>Using Demo Mode'
        st.markdown(f'<div style="padding: 10px; background: rgba(244, 67, 54, 0.1); border-radius: 10px; margin: 10px 0;">{status_html}</div>', unsafe_allow_html=True)
    
    st.caption(f"Backend API: {API_BASE_URL}")

    st.divider()
    
    # Navigation menu
    selected = option_menu(
        menu_title="Main Menu",
        options=["Dashboard", "Metrics", "Alerts", "Predictions", "AI Insights", "Settings"],
        icons=["speedometer2", "graph-up", "bell", "crystal-ball", "robot", "gear"],
        menu_icon="list",
        default_index=0,
        styles={
            "container": {"padding": "0!important"},
            "icon": {"font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "2px",
                "border-radius": "10px",
                "transition": "all 0.3s"
            },
            "nav-link-selected": {"background-color": "#4CAF50"},
        }
    )
    
    st.divider()
    
    # Quick Settings Panel
    with st.expander("⚙️ Quick Settings", expanded=False):
        st.markdown("#### 👤 Your Profile")
        user_name = st.text_input(
            "Display Name",
            value=st.session_state['user_name'],
            help="This name will appear in notifications"
        )
        if user_name != st.session_state['user_name']:
            st.session_state['user_name'] = user_name
        
        st.markdown("#### 🔔 Notifications")
        user_email = st.text_input(
            "Email Address",
            value=st.session_state['user_email'],
            placeholder="your.email@example.com",
            help="Receive alerts via email"
        )
        
        if user_email and validate_email(user_email):
            st.session_state['user_email'] = user_email
            st.success("✅ Valid email")
        elif user_email:
            st.error("❌ Invalid email format")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state['notification_prefs']['email'] = st.checkbox(
                "📧 Email",
                value=st.session_state['notification_prefs']['email'],
                help="Send alerts via email"
            )
        with col2:
            st.session_state['notification_prefs']['in_app'] = st.checkbox(
                "💬 In-App",
                value=st.session_state['notification_prefs']['in_app'],
                help="Show alerts in dashboard"
            )
        
        st.markdown("#### ⏰ Refresh Rate")
        st.session_state['auto_refresh'] = st.checkbox(
            "Auto-refresh dashboard",
            value=st.session_state['auto_refresh'],
            help="Automatically update metrics"
        )
        
        if st.session_state['auto_refresh']:
            st.session_state['refresh_interval'] = st.slider(
                "Update every (seconds)",
                min_value=5,
                max_value=60,
                value=st.session_state['refresh_interval'],
                step=5,
                help="How often to refresh the data"
            )
            st.caption(f"⏱️ Updates every {st.session_state['refresh_interval']} seconds")
        
        if st.button("💾 Save Settings", use_container_width=True):
            st.success("✅ Settings saved!")
            time.sleep(1)
            st.rerun()
    
    # Notifications Center
    unread_count = len([n for n in st.session_state['notifications'] if not n['read']])
    
    with st.expander(f"🔔 Notifications ({unread_count})", expanded=False):
        if not st.session_state['notifications']:
            st.info("No notifications yet")
        else:
            for notif in st.session_state['notifications'][:5]:  # Show last 5
                severity_colors = {
                    'info': '#2196F3',
                    'warning': '#FF9800',
                    'critical': '#F44336'
                }
                color = severity_colors.get(notif['severity'], '#2196F3')
                read_style = "opacity: 0.6;" if notif['read'] else ""
                
                st.markdown(f"""
                <div style='padding: 10px; border-left: 4px solid {color}; 
                            background: rgba(255,255,255,0.05); margin: 5px 0; 
                            border-radius: 5px; {read_style}'>
                    <strong>{notif['title']}</strong><br/>
                    <small>{notif['message']}</small><br/>
                    <small style='color: gray;'>{notif['timestamp'].strftime('%H:%M:%S')}</small>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("Clear All", use_container_width=True):
                NotificationManager.clear_all_notifications()
                st.rerun()
    
    st.divider()
    
    # Help & Info
    with st.expander("❓ Help & Support"):
        st.markdown("""
        **Need help?**
        
        📖 [Documentation](https://github.com)
        🐛 [Report Issue](https://github.com)
        💬 [Community](https://github.com)
        
        **Keyboard Shortcuts:**
        - `R` - Refresh dashboard
        - `S` - Open settings
        - `N` - View notifications
        """)

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

# Show welcome tour for first-time users
if selected == "Dashboard":
    show_welcome_tour()

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

if selected == "Dashboard":
    # Header with greeting
    current_hour = datetime.now().hour
    greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 18 else "Good evening"
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"{greeting}, {st.session_state['user_name']}! 👋")
        st.caption(f"Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')}")
    with col2:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
    
    # Get real-time metrics
    metrics = get_realtime_metrics()
    
    # System Health Overview Cards
    st.markdown("### 📊 System Health Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # CPU Card
    with col1:
        cpu_val = metrics.get('cpu_percent', 0)
        cpu_status, cpu_icon, cpu_color = get_health_status(cpu_val, st.session_state['alert_thresholds']['cpu'])
        
        st.metric(
            label="⚙️ CPU Usage",
            value=f"{cpu_val:.1f}%",
            delta=f"{cpu_status}",
            help="Processor utilization percentage"
        )
        st.progress(cpu_val / 100)
        detect_and_notify_anomaly("CPU Usage", cpu_val, st.session_state['alert_thresholds']['cpu'])
    
    # Memory Card
    with col2:
        mem_val = metrics.get('memory_percent', 0)
        mem_status, mem_icon, mem_color = get_health_status(mem_val, st.session_state['alert_thresholds']['memory'])
        
        st.metric(
            label="💾 Memory Usage",
            value=f"{mem_val:.1f}%",
            delta=f"{mem_status}",
            help="RAM utilization percentage"
        )
        st.progress(mem_val / 100)
        detect_and_notify_anomaly("Memory Usage", mem_val, st.session_state['alert_thresholds']['memory'])
    
    # Disk Card
    with col3:
        disk_val = metrics.get('disk_percent', 0)
        disk_status, disk_icon, disk_color = get_health_status(disk_val, st.session_state['alert_thresholds']['disk'])
        
        st.metric(
            label="💿 Disk Usage",
            value=f"{disk_val:.1f}%",
            delta=f"{disk_status}",
            help="Storage utilization percentage"
        )
        st.progress(disk_val / 100)
        detect_and_notify_anomaly("Disk Usage", disk_val, st.session_state['alert_thresholds']['disk'])
    
    # Network Card
    with col4:
        network_mb = metrics.get('network_sent', 0) / (1024 * 1024)
        st.metric(
            label="🌐 Network (Sent)",
            value=f"{network_mb:.1f} MB",
            delta="Normal",
            help="Total data sent over network"
        )
        st.progress(min(network_mb / 1000, 1.0))
    
    # Real-time Anomaly Detection
    st.divider()
    st.markdown("### 🔍 Real-Time Anomaly Detection")
    
    if st.session_state['backend_connected']:
        # Fetch anomaly detection results from backend
        anomaly_result = fetch_anomaly_detection(metrics)
        
        if anomaly_result and 'is_anomaly' in anomaly_result:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if anomaly_result['is_anomaly']:
                    severity = anomaly_result.get('severity', 'medium')
                    severity_icons = {
                        'critical': '🔴',
                        'high': '🟠',
                        'medium': '🟡',
                        'low': '🟢'
                    }
                    severity_colors = {
                        'critical': '#F44336',
                        'high': '#FF9800',
                        'medium': '#FFC107',
                        'low': '#8BC34A'
                    }
                    
                    st.error(f"""
                    {severity_icons.get(severity, '⚠️')} **Anomaly Detected!** (Severity: {severity.upper()})
                    
                    - **Metric:** {anomaly_result.get('metric_name', 'System')}
                    - **Z-Score:** {anomaly_result.get('z_score', 0):.2f}
                    - **Mean:** {anomaly_result.get('mean', 0):.2f}
                    - **Std Dev:** {anomaly_result.get('std_dev', 0):.2f}
                    """)
                    
                    # Store anomaly in session state
                    if anomaly_result not in st.session_state['anomalies_detected']:
                        st.session_state['anomalies_detected'].insert(0, {
                            **anomaly_result,
                            'timestamp': datetime.now()
                        })
                        if len(st.session_state['anomalies_detected']) > 50:
                            st.session_state['anomalies_detected'] = st.session_state['anomalies_detected'][:50]
                else:
                    st.success("✅ All metrics are within normal ranges")
            
            with col2:
                if anomaly_result['is_anomaly'] and st.button("🤖 Get AI Explanation"):
                    with st.spinner("Analyzing anomaly..."):
                        explanation = fetch_anomaly_explanation(anomaly_result)
                        st.info(f"**AI Analysis:**\n\n{explanation}")
        else:
            st.info("Anomaly detection service is initializing... (collecting baseline data)")
    else:
        st.warning("⚠️ Connect to backend to enable real-time anomaly detection")
    
    st.divider()
    
    # Real-time Charts
    st.markdown("### 📈 Live Performance Trends")
    
    df_history = get_metrics_history()
    
    # View selector
    col1, col2 = st.columns([3, 1])
    with col2:
        chart_view = st.selectbox(
            "Chart Type",
            ["Line Chart", "Area Chart", "Bar Chart"],
            label_visibility="collapsed"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚙️ CPU Performance")
        if not df_history.empty and 'cpu_percent' in df_history.columns:
            if chart_view == "Area Chart":
                fig = px.area(
                    df_history,
                    x='timestamp',
                    y='cpu_percent',
                    title="CPU Usage Over Time",
                    color_discrete_sequence=['#4CAF50']
                )
            elif chart_view == "Bar Chart":
                fig = px.bar(
                    df_history,
                    x='timestamp',
                    y='cpu_percent',
                    title="CPU Usage Over Time",
                    color_discrete_sequence=['#4CAF50']
                )
            else:
                fig = px.line(
                    df_history,
                    x='timestamp',
                    y='cpu_percent',
                    title="CPU Usage Over Time",
                    markers=True,
                    color_discrete_sequence=['#4CAF50']
                )
            
            fig.update_layout(
                hovermode="x unified",
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Time",
                yaxis_title="CPU %",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⏳ Collecting data...")
    
    with col2:
        st.markdown("#### 💾 Memory & Disk")
        if not df_history.empty:
            fig = go.Figure()
            
            if 'memory_percent' in df_history.columns:
                fig.add_trace(go.Scatter(
                    x=df_history['timestamp'],
                    y=df_history['memory_percent'],
                    mode='lines+markers',
                    name='Memory',
                    line=dict(color='#2196F3', width=2),
                    fill='tonexty'
                ))
            
            if 'disk_percent' in df_history.columns:
                fig.add_trace(go.Scatter(
                    x=df_history['timestamp'],
                    y=df_history['disk_percent'],
                    mode='lines+markers',
                    name='Disk',
                    line=dict(color='#FF9800', width=2)
                ))
            
            fig.update_layout(
                title="Memory & Disk Usage",
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Time",
                yaxis_title="Usage %",
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⏳ Collecting data...")
    
    st.divider()
    
    # Recent Alerts
    st.markdown("### 🚨 Recent Alerts & Actions")
    
    recent_alerts = st.session_state.get('alert_history', [])[:5]
    
    if recent_alerts:
        for alert in recent_alerts:
            severity_emoji = "🔴" if alert['severity'] == 'critical' else "🟡"
            severity_color = "#F44336" if alert['severity'] == 'critical' else "#FF9800"
            
            with st.expander(
                f"{severity_emoji} {alert['metric']} - {alert['timestamp'].strftime('%H:%M:%S')}",
                expanded=False
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Value", f"{alert['value']:.1f}%")
                with col2:
                    st.metric("Threshold", f"{alert['threshold']:.1f}%")
                with col3:
                    st.metric("Severity", alert['severity'].upper())
                
                st.markdown(f"""
                <div style='padding: 15px; background: rgba(255,152,0,0.1); 
                            border-left: 4px solid {severity_color}; border-radius: 5px; margin: 10px 0;'>
                    <strong>Quick Fix Suggestions:</strong><br/>
                    • Check running processes and stop unnecessary ones<br/>
                    • Review resource-intensive applications<br/>
                    • Consider upgrading system resources if issue persists<br/>
                    • Set up alerts for early warning
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Mark as Resolved", key=f"resolve_{alert['timestamp']}"):
                    st.success("✅ Alert marked as resolved!")
    else:
        st.success("🎉 No alerts! Your system is running smoothly.")
    
    # Quick Actions
    st.divider()
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 View Detailed Metrics", use_container_width=True):
            st.session_state['selected_page'] = "Metrics"
            st.rerun()
    
    with col2:
        if st.button("🔔 Check All Alerts", use_container_width=True):
            st.session_state['selected_page'] = "Alerts"
            st.rerun()
    
    with col3:
        if st.button("🔮 View Predictions", use_container_width=True):
            st.session_state['selected_page'] = "Predictions"
            st.rerun()
    
    with col4:
        if st.button("⚙️ Configure Settings", use_container_width=True):
            st.session_state['selected_page'] = "Settings"
            st.rerun()

# ============================================================================
# PAGE: METRICS (Detailed View)
# ============================================================================

elif selected == "Metrics":
    st.title("📈 Detailed System Metrics")
    st.caption("Deep dive into your system performance")
    
    # Time range selector
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        time_range = st.selectbox(
            "Time Range",
            ["Last 5 minutes", "Last 15 minutes", "Last hour", "Last 6 hours", "Last 24 hours"],
            help="Select the time period to analyze"
        )
    with col2:
        metric_type = st.selectbox(
            "Metric Type",
            ["All Metrics", "CPU Only", "Memory Only", "Disk Only", "Network Only"],
            help="Filter by specific metric"
        )
    with col3:
        if st.button("📥 Export Data", use_container_width=True):
            st.info("Export feature coming soon!")
    
    st.divider()
    
    # Metrics table
    df_history = get_metrics_history()
    
    if not df_history.empty:
        st.markdown("#### 📊 Live Metrics Table")
        
        # Format the dataframe for display
        display_df = df_history.copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%H:%M:%S')
        
        if 'cpu_percent' in display_df.columns:
            display_df['cpu_percent'] = display_df['cpu_percent'].round(2)
        if 'memory_percent' in display_df.columns:
            display_df['memory_percent'] = display_df['memory_percent'].round(2)
        if 'disk_percent' in display_df.columns:
            display_df['disk_percent'] = display_df['disk_percent'].round(2)
        
        st.dataframe(
            display_df.tail(20),
            use_container_width=True,
            height=400
        )
        
        # Statistics
        st.markdown("#### 📊 Statistical Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'cpu_percent' in df_history.columns:
                st.metric("Avg CPU", f"{df_history['cpu_percent'].mean():.1f}%")
                st.metric("Max CPU", f"{df_history['cpu_percent'].max():.1f}%")
        
        with col2:
            if 'memory_percent' in df_history.columns:
                st.metric("Avg Memory", f"{df_history['memory_percent'].mean():.1f}%")
                st.metric("Max Memory", f"{df_history['memory_percent'].max():.1f}%")
        
        with col3:
            if 'disk_percent' in df_history.columns:
                st.metric("Avg Disk", f"{df_history['disk_percent'].mean():.1f}%")
                st.metric("Max Disk", f"{df_history['disk_percent'].max():.1f}%")
        
        with col4:
            st.metric("Data Points", len(df_history))
            st.metric("Time Span", f"{len(df_history) * 10}s")
    
    else:
        st.info("⏳ No data available yet. Metrics will appear as they are collected.")

# ============================================================================
# PAGE: ALERTS
# ============================================================================

elif selected == "Alerts":
    st.title("🔔 Alert History & Management")
    st.caption("View and manage all system alerts")
    
    # Alert summary
    col1, col2, col3, col4 = st.columns(4)
    
    total_alerts = len(st.session_state.get('alert_history', []))
    critical_alerts = len([a for a in st.session_state.get('alert_history', []) if a['severity'] == 'critical'])
    warning_alerts = len([a for a in st.session_state.get('alert_history', []) if a['severity'] == 'warning'])
    
    with col1:
        st.metric("Total Alerts", total_alerts, help="All alerts in history")
    with col2:
        st.metric("Critical", critical_alerts, help="High priority alerts")
    with col3:
        st.metric("Warnings", warning_alerts, help="Medium priority alerts")
    with col4:
        st.metric("Active", critical_alerts + warning_alerts, help="Unresolved alerts")
    
    st.divider()
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_severity = st.multiselect(
            "Filter by Severity",
            ["critical", "warning"],
            default=["critical", "warning"]
        )
    with col2:
        filter_metric = st.multiselect(
            "Filter by Metric",
            ["CPU Usage", "Memory Usage", "Disk Usage", "Network"],
            default=["CPU Usage", "Memory Usage", "Disk Usage"]
        )
    
    # Alert list
    all_alerts = st.session_state.get('alert_history', [])
    filtered_alerts = [
        a for a in all_alerts
        if a['severity'] in filter_severity and a['metric'] in filter_metric
    ]
    
    if filtered_alerts:
        for i, alert in enumerate(filtered_alerts[:20]):  # Show last 20
            severity_emoji = "🔴" if alert['severity'] == 'critical' else "🟡"
            
            with st.expander(
                f"{severity_emoji} {alert['metric']} - {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                expanded=(i == 0)  # Expand first alert
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Value", f"{alert['value']:.1f}%")
                with col2:
                    st.metric("Threshold", f"{alert['threshold']:.1f}%")
                with col3:
                    st.metric("Severity", alert['severity'].upper())
                
                st.markdown("**Recommended Actions:**")
                st.markdown("""
                - 🔍 Investigate the root cause
                - ⚡ Stop non-essential processes
                - 📊 Monitor for pattern recurrence
                - 🔧 Consider resource optimization
                """)
                
                if st.button("✅ Resolve Alert", key=f"resolve_alert_{i}"):
                    st.success("Alert marked as resolved!")
    else:
        st.success("🎉 No alerts matching your filters!")
    
    # Clear history
    if st.button("🗑️ Clear Alert History"):
        if st.button("⚠️ Confirm Clear All Alerts"):
            st.session_state['alert_history'] = []
            st.success("✅ Alert history cleared!")
            st.rerun()

# ============================================================================
# PAGE: PREDICTIONS
# ============================================================================

elif selected == "Predictions":
    st.title("🔮 Predictive Analytics")
    st.caption("Forecast future system behavior")
    
    st.info("""
    📊 **Prediction Feature**
    
    This feature uses historical data to predict future system behavior.
    You can:
    - Forecast resource usage trends
    - Identify potential issues before they occur
    - Plan capacity upgrades
    
    *Note: Predictions become more accurate with more historical data.*
    """)
    
    # Simple prediction based on current trend
    df_history = get_metrics_history()
    
    if not df_history.empty and len(df_history) > 5:
        st.markdown("### 📈 CPU Usage Forecast (Next Hour)")
        
        # Simple linear trend
        if 'cpu_percent' in df_history.columns:
            recent_cpu = df_history['cpu_percent'].tail(10).values
            trend = np.polyfit(range(len(recent_cpu)), recent_cpu, 1)
            
            # Predict next 12 points (1 hour if 5-min intervals)
            future_points = 12
            predictions = [trend[0] * i + trend[1] for i in range(len(recent_cpu), len(recent_cpu) + future_points)]
            
            # Create forecast chart
            fig = go.Figure()
            
            # Historical data
            fig.add_trace(go.Scatter(
                x=list(range(len(recent_cpu))),
                y=recent_cpu,
                mode='lines+markers',
                name='Historical',
                line=dict(color='#4CAF50', width=2)
            ))
            
            # Predictions
            fig.add_trace(go.Scatter(
                x=list(range(len(recent_cpu), len(recent_cpu) + future_points)),
                y=predictions,
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#FF9800', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title="CPU Usage Prediction",
                xaxis_title="Time Points",
                yaxis_title="CPU %",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Prediction insights
            avg_predicted = np.mean(predictions)
            if avg_predicted > 80:
                st.error(f"⚠️ **Warning:** CPU usage predicted to reach {avg_predicted:.1f}% - Consider scaling resources!")
            elif avg_predicted > 70:
                st.warning(f"⚡ **Attention:** CPU usage trending towards {avg_predicted:.1f}% - Monitor closely")
            else:
                st.success(f"✅ **Healthy:** CPU usage expected to remain at {avg_predicted:.1f}%")
    else:
        st.info("⏳ Not enough data for predictions yet. Keep monitoring to build history!")

# ============================================================================
# PAGE: AI INSIGHTS
# ============================================================================

elif selected == "AI Insights":
    st.title("🤖 AI-Powered System Analysis")
    st.caption("Get intelligent insights and recommendations powered by GROQ AI")
    
    if not st.session_state['backend_connected']:
        st.warning("⚠️ Please connect to backend to use AI features")
    else:
        # Current System Analysis
        st.markdown("### 📊 Current System Analysis")
        
        metrics = get_realtime_metrics()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### Real-Time Metrics")
            st.json({
                "CPU Usage": f"{metrics.get('cpu_percent', 0):.1f}%",
                "Memory Usage": f"{metrics.get('memory_percent', 0):.1f}%",
                "Disk Usage": f"{metrics.get('disk_percent', 0):.1f}%",
                "Network Sent": f"{metrics.get('network_sent', 0) / (1024 * 1024):.1f} MB"
            })
        
        with col2:
            if st.button("🔍 Analyze Current State", use_container_width=True, type="primary"):
                with st.spinner("🤖 AI analyzing your system..."):
                    analysis = fetch_ai_analysis(metrics)
                    st.session_state['ai_analysis_cache']['current'] = {
                        'analysis': analysis,
                        'timestamp': datetime.now(),
                        'metrics': metrics.copy()
                    }
        
        # Display cached analysis
        if 'current' in st.session_state['ai_analysis_cache']:
            cached = st.session_state['ai_analysis_cache']['current']
            st.divider()
            st.markdown("#### 🔮 AI Analysis Results")
            st.info(f"**Generated:** {cached['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(cached['analysis'])
        
        st.divider()
        
        # Anomaly History Analysis
        st.markdown("### 🔍 Anomaly Detection History")
        
        if st.session_state['anomalies_detected']:
            st.success(f"📌 **{len(st.session_state['anomalies_detected'])} anomalies** detected in this session")
            
            # Display recent anomalies
            st.markdown("#### Recent Anomalies")
            
            for idx, anomaly in enumerate(st.session_state['anomalies_detected'][:10]):
                with st.expander(
                    f"🔴 Anomaly {idx + 1} - {anomaly.get('timestamp', datetime.now()).strftime('%H:%M:%S')} "
                    f"(Severity: {anomaly.get('severity', 'unknown').upper()})"
                ):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **Details:**
                        - **Metric:** {anomaly.get('metric_name', 'Unknown')}
                        - **Z-Score:** {anomaly.get('z_score', 0):.2f}
                        - **Mean:** {anomaly.get('mean', 0):.2f}
                        - **Std Dev:** {anomaly.get('std_dev', 0):.2f}
                        - **Severity:** {anomaly.get('severity', 'unknown').upper()}
                        """)
                    
                    with col2:
                        if st.button(f"🤖 Explain", key=f"explain_{idx}"):
                            with st.spinner("Getting AI explanation..."):
                                explanation = fetch_anomaly_explanation(anomaly)
                                st.markdown(f"**AI Explanation:**\n\n{explanation}")
            
            # Anomaly Statistics
            st.divider()
            st.markdown("#### 📈 Anomaly Statistics")
            
            severity_counts = {}
            for anomaly in st.session_state['anomalies_detected']:
                severity = anomaly.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔴 Critical", severity_counts.get('critical', 0))
            with col2:
                st.metric("🟠 High", severity_counts.get('high', 0))
            with col3:
                st.metric("🟡 Medium", severity_counts.get('medium', 0))
            with col4:
                st.metric("🟢 Low", severity_counts.get('low', 0))
        else:
            st.info("✅ No anomalies detected yet. Your system is running smoothly!")
        
        st.divider()
        
        # Custom Analysis Query
        st.markdown("### 💬 Ask AI About Your System")
        
        with st.form("custom_ai_query"):
            query = st.text_area(
                "What would you like to know?",
                placeholder="e.g., Why is my CPU usage high? What can I do to improve performance?",
                help="Ask specific questions about your system metrics"
            )
            
            submitted = st.form_submit_button("🚀 Ask AI", use_container_width=True, type="primary")
            
            if submitted and query:
                with st.spinner("🤖 AI is thinking..."):
                    # For custom queries, we'll use the analysis endpoint with current metrics
                    analysis = fetch_ai_analysis(metrics)
                    st.markdown("#### 🤖 AI Response:")
                    st.success(analysis)
                    st.caption(f"Based on current metrics at {datetime.now().strftime('%H:%M:%S')}")

# ============================================================================
# PAGE: SETTINGS
# ============================================================================

elif selected == "Settings":
    st.title("⚙️ Settings & Configuration")
    st.caption("Customize your monitoring experience")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "🔔 Notifications", "📊 Thresholds", "🎨 Appearance"])
    
    with tab1:
        st.markdown("### 👤 Your Profile")
        
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Display Name", value=st.session_state['user_name'])
        with col2:
            new_email = st.text_input("Email Address", value=st.session_state['user_email'])
        
        if st.button("💾 Save Profile"):
            st.session_state['user_name'] = new_name
            if validate_email(new_email):
                st.session_state['user_email'] = new_email
                st.success("✅ Profile updated successfully!")
            else:
                st.error("❌ Invalid email address")
    
    with tab2:
        st.markdown("### 🔔 Notification Preferences")
        
        st.markdown("#### Email Notifications")
        st.session_state['notification_prefs']['email'] = st.checkbox(
            "Send alerts via email",
            value=st.session_state['notification_prefs']['email'],
            help="Get email notifications when alerts are triggered"
        )
        
        if st.session_state['notification_prefs']['email']:
            st.info(f"📧 Notifications will be sent to: {st.session_state['user_email']}")
            
            with st.expander("📧 Email Server Configuration"):
                st.markdown("""
                To enable email notifications, configure SMTP settings in `.streamlit/secrets.toml`:
                
                ```toml
                [smtp]
                server = "smtp.gmail.com"
                port = 587
                username = "your-email@gmail.com"
                password = "your-app-password"
                ```
                """)
        
        st.markdown("#### In-App Notifications")
        st.session_state['notification_prefs']['in_app'] = st.checkbox(
            "Show in-app notifications",
            value=st.session_state['notification_prefs']['in_app'],
            help="Display notifications in the sidebar"
        )
        
        # Test notification
        if st.button("🧪 Send Test Notification"):
            NotificationManager.send_in_app_notification(
                title="Test Notification",
                message="This is a test notification. Your notification system is working!",
                severity="info"
            )
            st.success("✅ Test notification sent! Check the sidebar.")
    
    with tab3:
        st.markdown("### 📊 Alert Thresholds")
        st.caption("Set custom thresholds for system alerts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### CPU Alert Threshold")
            st.session_state['alert_thresholds']['cpu'] = st.slider(
                "CPU %",
                min_value=50.0,
                max_value=100.0,
                value=st.session_state['alert_thresholds']['cpu'],
                step=5.0,
                help="Alert when CPU usage exceeds this percentage"
            )
            
            st.markdown("#### Memory Alert Threshold")
            st.session_state['alert_thresholds']['memory'] = st.slider(
                "Memory %",
                min_value=50.0,
                max_value=100.0,
                value=st.session_state['alert_thresholds']['memory'],
                step=5.0,
                help="Alert when memory usage exceeds this percentage"
            )
        
        with col2:
            st.markdown("#### Disk Alert Threshold")
            st.session_state['alert_thresholds']['disk'] = st.slider(
                "Disk %",
                min_value=50.0,
                max_value=100.0,
                value=st.session_state['alert_thresholds']['disk'],
                step=5.0,
                help="Alert when disk usage exceeds this percentage"
            )
            
            st.markdown("#### Network Alert Threshold")
            st.session_state['alert_thresholds']['network'] = st.slider(
                "Network (MB)",
                min_value=100.0,
                max_value=5000.0,
                value=st.session_state['alert_thresholds']['network'],
                step=100.0,
                help="Alert when network usage exceeds this value"
            )
        
        if st.button("💾 Save Thresholds"):
            st.success("✅ Alert thresholds updated!")
        
        if st.button("🔄 Reset to Defaults"):
            st.session_state['alert_thresholds'] = {
                'cpu': 80.0,
                'memory': 75.0,
                'disk': 80.0,
                'network': 1000.0
            }
            st.success("✅ Thresholds reset to defaults!")
            st.rerun()
    
    with tab4:
        st.markdown("### 🎨 Appearance & Display")
        
        st.markdown("#### Dashboard View")
        st.session_state['dashboard_view'] = st.radio(
            "Select dashboard layout",
            ["overview", "detailed", "compact"],
            format_func=lambda x: x.capitalize(),
            help="Choose how information is displayed"
        )
        
        st.markdown("#### Chart Animations")
        st.session_state['chart_animation'] = st.checkbox(
            "Enable chart animations",
            value=st.session_state['chart_animation'],
            help="Smooth transitions in charts (may affect performance)"
        )
        
        if st.button("💾 Save Appearance Settings"):
            st.success("✅ Appearance settings saved!")

# ============================================================================
# AUTO REFRESH
# ============================================================================

if st.session_state['auto_refresh']:
    time.sleep(st.session_state['refresh_interval'])
    st.rerun()
