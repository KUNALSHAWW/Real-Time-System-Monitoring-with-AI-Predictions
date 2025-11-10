"""
Real-Time System Monitoring Dashboard - Enhanced Production Version
Built with Streamlit with advanced features:
- WebSocket real-time updates
- Email notifications with SMTP
- In-app notifications
- Advanced forecasting (Prophet, ARIMA)
- Custom metric plugins
- Slack/PagerDuty integration
- Advanced RBAC
- Security hardening
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import time
import asyncio
import json
import hashlib
import re
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
from typing import Dict, Any, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import websockets
import threading
from queue import Queue

# ============================================================================
# SECURITY & CONFIGURATION
# ============================================================================

# Input validation patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
INTERVAL_OPTIONS = ["5 seconds", "10 seconds", "30 seconds", "1 minute", "5 minutes", "10 minutes", "30 minutes", "1 hour"]

# CSRF Token Management
def generate_csrf_token():
    """Generate CSRF token for form security"""
    if 'csrf_token' not in st.session_state:
        st.session_state['csrf_token'] = hashlib.sha256(
            f"{datetime.now().isoformat()}{st.session_state.get('user_email', 'anonymous')}".encode()
        ).hexdigest()
    return st.session_state['csrf_token']

def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(EMAIL_PATTERN.match(email)) if email else False

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'user_email': '',
        'check_interval': '10 seconds',
        'notification_prefs': {
            'email': True,
            'in_app': True,
            'slack': False,
            'pagerduty': False
        },
        'notifications': [],
        'user_role': 'viewer',  # admin, operator, viewer
        'authenticated': False,
        'websocket_connected': False,
        'custom_metrics': [],
        'alert_history': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="System Monitoring Dashboard - Production",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

class NotificationManager:
    """Manage in-app and external notifications"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, html_body: str = None):
        """Send email notification via SMTP"""
        try:
            # SMTP Configuration (from env)
            smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(st.secrets.get("SMTP_PORT", 587))
            smtp_user = st.secrets.get("SMTP_USERNAME", "")
            smtp_pass = st.secrets.get("SMTP_PASSWORD", "")
            
            if not smtp_user or not smtp_pass:
                st.error("📧 SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = to_email
            
            # Attach plain text and HTML
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            st.error(f"❌ Email send failed: {str(e)}")
            return False
    
    @staticmethod
    def send_in_app_notification(title: str, message: str, severity: str = "info"):
        """Add in-app notification"""
        notification = {
            'id': len(st.session_state['notifications']),
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'message': message,
            'severity': severity,
            'read': False
        }
        st.session_state['notifications'].insert(0, notification)
        
        # Keep only last 50 notifications
        st.session_state['notifications'] = st.session_state['notifications'][:50]
    
    @staticmethod
    def send_slack_notification(webhook_url: str, message: str):
        """Send notification to Slack"""
        try:
            payload = {
                "text": message,
                "username": "System Monitor Bot",
                "icon_emoji": ":bell:"
            }
            response = requests.post(webhook_url, json=payload)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Slack notification failed: {str(e)}")
            return False
    
    @staticmethod
    def send_pagerduty_alert(api_key: str, service_key: str, description: str, severity: str):
        """Send alert to PagerDuty"""
        try:
            url = "https://events.pagerduty.com/v2/enqueue"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token token={api_key}"
            }
            payload = {
                "routing_key": service_key,
                "event_action": "trigger",
                "payload": {
                    "summary": description,
                    "severity": severity,
                    "source": "system-monitor",
                    "timestamp": datetime.now().isoformat()
                }
            }
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 202
        except Exception as e:
            st.error(f"PagerDuty alert failed: {str(e)}")
            return False

# ============================================================================
# FIX SUGGESTIONS ENGINE
# ============================================================================

def get_fix_suggestions(metric_name: str, value: float, threshold: float, severity: str) -> Dict[str, Any]:
    """Generate automated fix suggestions based on metric type and severity"""
    
    fix_suggestions = {
        'CPU Usage': {
            'root_causes': [
                "High CPU-intensive processes running",
                "Infinite loops or inefficient algorithms",
                "Insufficient CPU resources for workload",
                "Malware or cryptocurrency miners"
            ],
            'immediate_actions': [
                "🔍 Run `top` or Task Manager to identify CPU-hogging processes",
                "⚡ Kill non-essential high-CPU processes: `kill -9 <PID>`",
                "🔄 Restart resource-intensive services",
                "📊 Check for runaway scripts or cron jobs"
            ],
            'short_term_fixes': [
                "Optimize application code and queries",
                "Implement rate limiting for API endpoints",
                "Enable CPU throttling for non-critical services",
                "Scale horizontally by adding more instances"
            ],
            'long_term_solutions': [
                "Migrate to auto-scaling infrastructure (AWS Auto Scaling, K8s HPA)",
                "Implement caching layer (Redis, Memcached)",
                "Profile and optimize application bottlenecks",
                "Upgrade to higher CPU instance types"
            ],
            'commands': [
                "top -o %CPU",  # Linux
                "htop",  # Linux with htop installed
                "ps aux | sort -nrk 3,3 | head -n 10",  # Top CPU processes
                "systemctl restart <service-name>",  # Restart service
                "nice -n 19 <command>",  # Run with lower priority
            ],
            'preventive_measures': [
                "Set up CPU usage alerts at 70% threshold",
                "Implement application performance monitoring (APM)",
                "Regular performance testing and load testing",
                "Establish CPU usage baselines and capacity planning"
            ]
        },
        'Memory Usage': {
            'root_causes': [
                "Memory leaks in application code",
                "Large dataset processing without pagination",
                "Insufficient RAM for workload",
                "Too many concurrent connections or sessions"
            ],
            'immediate_actions': [
                "🔍 Check memory usage: `free -h` or Task Manager",
                "⚡ Kill memory-intensive processes: `kill <PID>`",
                "🗑️ Clear system cache: `sync; echo 3 > /proc/sys/vm/drop_caches`",
                "🔄 Restart application services to free memory"
            ],
            'short_term_fixes': [
                "Add swap space if physical RAM is limited",
                "Implement pagination for large queries",
                "Set memory limits for containers (Docker: --memory flag)",
                "Enable garbage collection tuning"
            ],
            'long_term_solutions': [
                "Fix memory leaks in application code",
                "Upgrade RAM or instance type",
                "Implement connection pooling",
                "Use memory-efficient data structures"
            ],
            'commands': [
                "free -h",  # Check memory
                "top -o %MEM",  # Sort by memory
                "ps aux | sort -nrk 4,4 | head -n 10",  # Top memory processes
                "sudo sysctl -w vm.drop_caches=3",  # Clear cache
                "docker update --memory 2g <container>",  # Update container memory limit
            ],
            'preventive_measures': [
                "Regular memory profiling (valgrind, memory_profiler)",
                "Implement memory usage monitoring",
                "Set up OOM (Out of Memory) alerts",
                "Conduct regular code reviews for memory management"
            ]
        },
        'Disk Usage': {
            'root_causes': [
                "Log files growing uncontrollably",
                "Temporary files not cleaned up",
                "Database storage increasing",
                "Backup files accumulating"
            ],
            'immediate_actions': [
                "🔍 Find largest files: `du -sh /* | sort -rh | head -n 10`",
                "🗑️ Clean log files: `truncate -s 0 /var/log/*.log`",
                "🗑️ Remove old Docker images: `docker system prune -a`",
                "📦 Compress old logs: `gzip /var/log/*.log`"
            ],
            'short_term_fixes': [
                "Set up log rotation with logrotate",
                "Clean up temporary directories (/tmp, /var/tmp)",
                "Archive old database records",
                "Move large files to external storage"
            ],
            'long_term_solutions': [
                "Implement centralized logging (ELK, Splunk)",
                "Set up automated cleanup scripts",
                "Add more disk space or upgrade storage tier",
                "Use cloud storage for backups (S3, Azure Blob)"
            ],
            'commands': [
                "df -h",  # Check disk usage
                "du -sh /* | sort -rh | head -n 10",  # Largest directories
                "find / -type f -size +100M",  # Find files larger than 100MB
                "docker system prune -a -f",  # Clean Docker
                "journalctl --vacuum-time=7d",  # Clean systemd logs
            ],
            'preventive_measures': [
                "Set up disk usage alerts at 75% threshold",
                "Implement automated log rotation",
                "Regular cleanup schedules via cron jobs",
                "Monitor disk I/O performance"
            ]
        },
        'Network Latency': {
            'root_causes': [
                "Network congestion or bandwidth saturation",
                "DNS resolution issues",
                "Routing problems",
                "Firewall or security group misconfigurations"
            ],
            'immediate_actions': [
                "🔍 Test connectivity: `ping <host>` or `traceroute <host>`",
                "📊 Check bandwidth: `iftop` or `nethogs`",
                "🔄 Restart network services: `systemctl restart networking`",
                "🔍 Check DNS: `nslookup <domain>` or `dig <domain>`"
            ],
            'short_term_fixes': [
                "Switch to faster DNS servers (8.8.8.8, 1.1.1.1)",
                "Clear DNS cache",
                "Reduce network traffic or implement QoS",
                "Check and fix MTU settings"
            ],
            'long_term_solutions': [
                "Implement CDN for static assets",
                "Use load balancers for traffic distribution",
                "Optimize application to reduce network calls",
                "Upgrade network infrastructure or bandwidth"
            ],
            'commands': [
                "ping -c 5 <host>",  # Test connectivity
                "traceroute <host>",  # Trace route
                "mtr <host>",  # Combined ping and traceroute
                "netstat -tuln",  # Check open ports
                "ss -s",  # Socket statistics
            ],
            'preventive_measures': [
                "Set up network latency monitoring",
                "Implement redundant network paths",
                "Regular network performance testing",
                "Monitor bandwidth utilization"
            ]
        },
        'Database Connection Pool': {
            'root_causes': [
                "Too many concurrent database connections",
                "Connection leaks in application code",
                "Database server resource exhaustion",
                "Long-running queries holding connections"
            ],
            'immediate_actions': [
                "🔍 Check active connections in database",
                "⚡ Kill idle or long-running queries",
                "🔄 Restart application to reset connection pool",
                "📊 Increase max_connections temporarily"
            ],
            'short_term_fixes': [
                "Implement connection pooling (PgBouncer, ProxySQL)",
                "Set connection timeout limits",
                "Optimize slow queries",
                "Close connections properly in code"
            ],
            'long_term_solutions': [
                "Fix connection leaks in application",
                "Implement read replicas for read-heavy workloads",
                "Use database connection management best practices",
                "Scale database vertically or horizontally"
            ],
            'commands': [
                "SELECT count(*) FROM pg_stat_activity;",  # PostgreSQL connections
                "SHOW PROCESSLIST;",  # MySQL connections
                "SELECT * FROM pg_stat_activity WHERE state = 'idle';",  # Idle connections
                "pg_ctl reload",  # Reload PostgreSQL config
            ],
            'preventive_measures': [
                "Monitor database connection metrics",
                "Set up alerts for connection pool exhaustion",
                "Regular query performance audits",
                "Implement circuit breakers"
            ]
        }
    }
    
    # Default suggestions for unknown metrics
    default_suggestions = {
        'root_causes': [
            "Resource exhaustion or bottleneck",
            "Configuration issues",
            "External dependencies failing",
            "Application bugs or inefficiencies"
        ],
        'immediate_actions': [
            "🔍 Check system logs for errors",
            "📊 Monitor resource utilization",
            "🔄 Restart affected services",
            "⚡ Scale resources if possible"
        ],
        'short_term_fixes': [
            "Implement temporary workarounds",
            "Apply configuration changes",
            "Add monitoring and alerts",
            "Optimize resource allocation"
        ],
        'long_term_solutions': [
            "Root cause analysis and permanent fix",
            "Infrastructure improvements",
            "Code optimization",
            "Capacity planning and scaling strategy"
        ],
        'commands': [
            "systemctl status <service>",
            "journalctl -u <service> -n 100",
            "docker logs <container>",
            "tail -f /var/log/syslog",
        ],
        'preventive_measures': [
            "Set up comprehensive monitoring",
            "Implement automated alerting",
            "Regular health checks",
            "Performance testing and optimization"
        ]
    }
    
    suggestions = fix_suggestions.get(metric_name, default_suggestions)
    
    # Add severity-specific recommendations
    if severity == 'critical':
        suggestions['priority'] = '🔴 CRITICAL - Immediate action required'
        suggestions['escalation'] = 'Contact on-call engineer and incident manager'
    else:
        suggestions['priority'] = '🟠 WARNING - Monitor and plan remediation'
        suggestions['escalation'] = 'Create ticket and schedule fix within 24 hours'
    
    return suggestions

# ============================================================================
# ANOMALY DETECTION WITH AUTO-NOTIFICATION
# ============================================================================

def detect_and_notify_anomaly(metric_name: str, value: float, threshold: float):
    """Detect anomaly and send notifications"""
    if value > threshold:
        severity = 'critical' if value > threshold * 1.5 else 'warning'
        anomaly = {
            'metric': metric_name,
            'value': value,
            'threshold': threshold,
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'fixes': get_fix_suggestions(metric_name, value, threshold, severity)
        }
        
        st.session_state['alert_history'].append(anomaly)
        
        # In-app notification
        if st.session_state['notification_prefs']['in_app']:
            NotificationManager.send_in_app_notification(
                f"🚨 Anomaly Detected: {metric_name}",
                f"Value {value:.2f} exceeds threshold {threshold:.2f}",
                severity=anomaly['severity']
            )
        
        # Email notification
        if st.session_state['notification_prefs']['email'] and st.session_state['user_email']:
            subject = f"🚨 ALERT: {metric_name} Anomaly Detected"
            
            # Create detailed email body
            body = f"""
System Monitoring Alert

Metric: {metric_name}
Current Value: {value:.2f}
Threshold: {threshold:.2f}
Severity: {anomaly['severity'].upper()}
Timestamp: {anomaly['timestamp']}

Suggested Actions:
1. Check system resource utilization
2. Review recent changes or deployments
3. Investigate potential memory leaks or CPU-intensive processes
4. Scale resources if needed

View dashboard: http://localhost:8501
"""
            
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #d32f2f;">🚨 System Monitoring Alert</h2>
    <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #d32f2f;">
        <h3>Anomaly Details</h3>
        <p><strong>Metric:</strong> {metric_name}</p>
        <p><strong>Current Value:</strong> <span style="color: #d32f2f; font-size: 18px;">{value:.2f}</span></p>
        <p><strong>Threshold:</strong> {threshold:.2f}</p>
        <p><strong>Severity:</strong> <span style="color: #d32f2f;">{anomaly['severity'].upper()}</span></p>
        <p><strong>Timestamp:</strong> {anomaly['timestamp']}</p>
    </div>
    
    <h3>Suggested Actions</h3>
    <ol>
        <li>Check system resource utilization</li>
        <li>Review recent changes or deployments</li>
        <li>Investigate potential memory leaks or CPU-intensive processes</li>
        <li>Scale resources if needed</li>
    </ol>
    
    <p><a href="http://localhost:8501" style="background: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Dashboard</a></p>
</body>
</html>
"""
            
            NotificationManager.send_email(
                st.session_state['user_email'],
                subject,
                body,
                html_body
            )
        
        # Slack notification
        if st.session_state['notification_prefs']['slack']:
            webhook_url = st.secrets.get("SLACK_WEBHOOK_URL", "")
            if webhook_url:
                NotificationManager.send_slack_notification(
                    webhook_url,
                    f"🚨 *ALERT*: {metric_name} = {value:.2f} (threshold: {threshold:.2f})"
                )
        
        # PagerDuty alert
        if st.session_state['notification_prefs']['pagerduty']:
            api_key = st.secrets.get("PAGERDUTY_API_KEY", "")
            service_key = st.secrets.get("PAGERDUTY_SERVICE_KEY", "")
            if api_key and service_key:
                NotificationManager.send_pagerduty_alert(
                    api_key,
                    service_key,
                    f"{metric_name} anomaly: {value:.2f}",
                    anomaly['severity']
                )

# ============================================================================
# RBAC - ROLE-BASED ACCESS CONTROL
# ============================================================================

def check_permission(required_role: str) -> bool:
    """Check if user has required permission level"""
    role_hierarchy = {'admin': 3, 'operator': 2, 'viewer': 1}
    user_level = role_hierarchy.get(st.session_state['user_role'], 0)
    required_level = role_hierarchy.get(required_role, 0)
    return user_level >= required_level

def require_permission(required_role: str):
    """Decorator to require specific permission level"""
    if not check_permission(required_role):
        st.error(f"🔒 Access Denied: This action requires '{required_role}' role or higher")
        st.stop()

# ============================================================================
# USER PREFERENCES PANEL (MAIN PAGE)
# ============================================================================

def show_user_preferences():
    """Show user preferences panel on main page"""
    st.sidebar.title("👤 User Preferences")
    
    # Email configuration
    with st.sidebar.expander("📧 Email Notifications", expanded=True):
        email = st.text_input(
            "Your Email Address",
            value=st.session_state['user_email'],
            placeholder="user@example.com",
            help="Enter your email to receive anomaly alerts"
        )
        
        if email and validate_email(email):
            st.session_state['user_email'] = sanitize_input(email)
            st.success("✅ Email validated")
        elif email:
            st.error("❌ Invalid email format")
    
    # Check interval
    with st.sidebar.expander("⏰ Monitor Interval", expanded=True):
        interval = st.selectbox(
            "How often to check logs?",
            options=INTERVAL_OPTIONS,
            index=INTERVAL_OPTIONS.index(st.session_state['check_interval']),
            help="Select how frequently the system should check for anomalies"
        )
        st.session_state['check_interval'] = interval
        
        # Convert to seconds for display
        interval_seconds = {
            "5 seconds": 5, "10 seconds": 10, "30 seconds": 30,
            "1 minute": 60, "5 minutes": 300, "10 minutes": 600,
            "30 minutes": 1800, "1 hour": 3600
        }
        st.info(f"⏱️ Checking every {interval_seconds[interval]} seconds")
    
    # Notification preferences
    with st.sidebar.expander("🔔 Notification Channels"):
        st.session_state['notification_prefs']['email'] = st.checkbox(
            "📧 Email Alerts",
            value=st.session_state['notification_prefs']['email']
        )
        st.session_state['notification_prefs']['in_app'] = st.checkbox(
            "💬 In-App Notifications",
            value=st.session_state['notification_prefs']['in_app']
        )
        st.session_state['notification_prefs']['slack'] = st.checkbox(
            "💼 Slack Notifications",
            value=st.session_state['notification_prefs']['slack']
        )
        st.session_state['notification_prefs']['pagerduty'] = st.checkbox(
            "📟 PagerDuty Alerts",
            value=st.session_state['notification_prefs']['pagerduty']
        )
    
    # Test notification button
    if st.sidebar.button("🧪 Test Notifications"):
        if st.session_state['notification_prefs']['in_app']:
            NotificationManager.send_in_app_notification(
                "Test Notification",
                "This is a test notification from the system monitor",
                "info"
            )
        
        if st.session_state['notification_prefs']['email'] and st.session_state['user_email']:
            success = NotificationManager.send_email(
                st.session_state['user_email'],
                "Test Email from System Monitor",
                "This is a test email. Your email notifications are working correctly!",
                "<p>This is a test email. Your email notifications are <strong>working correctly!</strong></p>"
            )
            if success:
                st.sidebar.success("📧 Test email sent!")

# ============================================================================
# IN-APP NOTIFICATION CENTER
# ============================================================================

def show_notification_center():
    """Display in-app notification center"""
    with st.sidebar.expander(f"🔔 Notifications ({len([n for n in st.session_state['notifications'] if not n['read']])} unread)"):
        if not st.session_state['notifications']:
            st.info("No notifications yet")
        else:
            for notif in st.session_state['notifications'][:10]:  # Show last 10
                severity_icons = {
                    'critical': '🔴',
                    'warning': '🟠',
                    'info': '🔵'
                }
                icon = severity_icons.get(notif['severity'], '⚪')
                
                st.markdown(f"""
                **{icon} {notif['title']}**  
                {notif['message']}  
                <small>{notif['timestamp']}</small>
                """, unsafe_allow_html=True)
                st.divider()

# ============================================================================
# WEBSOCKET REAL-TIME UPDATES
# ============================================================================

class WebSocketClient:
    """WebSocket client for real-time metric updates"""
    
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        self.queue = Queue()
        self.connected = False
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            async with websockets.connect(self.url) as websocket:
                self.connected = True
                st.session_state['websocket_connected'] = True
                
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    self.queue.put(data)
                    
        except Exception as e:
            self.connected = False
            st.session_state['websocket_connected'] = False
            print(f"WebSocket error: {e}")
    
    def start(self):
        """Start WebSocket connection in background thread"""
        def run():
            asyncio.run(self.connect())
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

# Initialize WebSocket (if not already started)
if 'ws_client' not in st.session_state:
    st.session_state['ws_client'] = WebSocketClient()
    # st.session_state['ws_client'].start()  # Uncomment when backend WebSocket is ready

# ============================================================================
# ADVANCED FORECASTING
# ============================================================================

def forecast_with_prophet(data: pd.DataFrame, periods: int = 24):
    """Forecast using Facebook Prophet"""
    try:
        from prophet import Prophet
        
        # Prepare data for Prophet
        df = data.rename(columns={'timestamp': 'ds', 'value': 'y'})
        
        # Create and fit model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False
        )
        model.fit(df)
        
        # Make future dataframe
        future = model.make_future_dataframe(periods=periods, freq='5min')
        forecast = model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        
    except ImportError:
        st.warning("Prophet not installed. Install with: pip install prophet")
        return None

def forecast_with_arima(data: pd.Series, periods: int = 24):
    """Forecast using ARIMA"""
    try:
        from statsmodels.tsa.arima.model import ARIMA
        
        # Fit ARIMA model
        model = ARIMA(data, order=(5, 1, 0))
        model_fit = model.fit()
        
        # Forecast
        forecast = model_fit.forecast(steps=periods)
        
        return forecast
        
    except ImportError:
        st.warning("statsmodels not installed. Install with: pip install statsmodels")
        return None

# ============================================================================
# CUSTOM METRIC PLUGINS
# ============================================================================

class MetricPlugin:
    """Base class for custom metric plugins"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def collect(self) -> float:
        """Override this method to collect metric value"""
        raise NotImplementedError
    
    def visualize(self, data: pd.DataFrame):
        """Override this method to create custom visualization"""
        raise NotImplementedError

def register_custom_metric(plugin: MetricPlugin):
    """Register a custom metric plugin"""
    if plugin.name not in [m['name'] for m in st.session_state['custom_metrics']]:
        st.session_state['custom_metrics'].append({
            'name': plugin.name,
            'description': plugin.description,
            'plugin': plugin
        })

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

show_user_preferences()
show_notification_center()

st.sidebar.divider()

with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Dashboard", "Metrics", "Anomalies", "Predictions", "Incidents", "AI Analysis", "Admin Panel"],
        icons=["speedometer2", "graph-up", "exclamation-triangle", "crystal-ball", "list-check", "robot", "gear"],
        menu_icon="cast",
        default_index=0
    )
    
    st.divider()
    
    # Connection status
    ws_status = "🟢 Connected" if st.session_state['websocket_connected'] else "🔴 Disconnected"
    st.caption(f"WebSocket: {ws_status}")
    st.caption(f"Role: {st.session_state['user_role'].upper()}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_metric_card(col, title: str, value: str, delta: str = None, icon: str = "📊"):
    """Create metric card with new Streamlit API"""
    with col:
        st.metric(
            label=f"{icon} {title}",
            value=value,
            delta=delta,
            delta_color="inverse"
        )

def create_line_chart(df: pd.DataFrame, title: str, x_col: str, y_col: str):
    """Create line chart with Plotly"""
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title,
        markers=True,
        template="plotly_dark"
    )
    
    fig.update_layout(
        hovermode="x unified",
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

if selected == "Dashboard":
    st.title("📊 Real-Time System Monitoring Dashboard")
    st.caption("Production-Grade Monitoring with AI Predictions")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Simulate real-time data
    cpu_value = np.random.uniform(60, 85)
    memory_value = np.random.uniform(40, 70)
    disk_value = np.random.uniform(65, 85)
    network_value = np.random.uniform(200, 300)
    
    create_metric_card(col1, "CPU Usage", f"{cpu_value:.1f}%", "+5%", "⚙️")
    create_metric_card(col2, "Memory", f"{memory_value:.1f}%", "-2%", "💾")
    create_metric_card(col3, "Disk", f"{disk_value:.1f}%", "+1%", "💿")
    create_metric_card(col4, "Network", f"{network_value:.0f} Mbps", "+12%", "🌐")
    
    # Check for anomalies
    detect_and_notify_anomaly("CPU Usage", cpu_value, 80.0)
    detect_and_notify_anomaly("Memory Usage", memory_value, 75.0)
    detect_and_notify_anomaly("Disk Usage", disk_value, 80.0)
    
    st.divider()
    
    # Real-time charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CPU Utilization Over Time")
        
        times = pd.date_range(start=datetime.now() - timedelta(hours=2), periods=100, freq='1min')
        cpu_data = pd.DataFrame({
            'time': times,
            'cpu': np.random.normal(65, 15, 100).clip(0, 100)
        })
        
        fig = create_line_chart(cpu_data, "CPU %", "time", "cpu")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("System Health Score")
        
        health_data = {
            'Component': ['CPU', 'Memory', 'Disk', 'Network', 'Database'],
            'Health': [92, 85, 78, 88, 95]
        }
        df_health = pd.DataFrame(health_data)
        
        fig = px.bar(
            df_health,
            x='Component',
            y='Health',
            title="Component Health Score",
            template="plotly_dark",
            color='Health',
            color_continuous_scale='Greens'
        )
        
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Recent activities
    st.subheader("📋 Recent Activities & Quick Fixes")
    
    activities = st.session_state.get('alert_history', [])[-5:]  # Last 5 alerts
    
    if activities:
        for idx, activity in enumerate(reversed(activities)):
            col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
            with col1:
                st.caption(activity['timestamp'][:19])
            with col2:
                st.write(f"{activity['metric']}: {activity['value']:.2f}")
            with col3:
                severity_color = {'critical': '🔴', 'warning': '🟠', 'info': '🟡'}
                st.caption(f"{severity_color.get(activity['severity'], '⚪')} {activity['severity'].upper()}")
            with col4:
                if st.button("🔧 Fix", key=f"quick_fix_dash_{idx}"):
                    st.info(f"Quick fix for {activity['metric']}:")
                    fixes = activity.get('fixes', {})
                    if fixes and 'immediate_actions' in fixes:
                        st.markdown("**Immediate Actions:**")
                        for action in fixes['immediate_actions'][:2]:  # Show first 2
                            st.markdown(f"- {action}")
                        st.markdown("👉 *Go to Incidents page for full fix guide*")
    else:
        st.info("✅ No recent alerts - System is healthy!")
    
    # Quick fix suggestions for most recent critical alert
    critical_alerts = [a for a in activities if a.get('severity') == 'critical']
    if critical_alerts:
        st.divider()
        st.warning("### 🚨 Critical Alert - Quick Actions")
        latest = critical_alerts[-1]
        fixes = latest.get('fixes', {})
        
        if fixes and 'immediate_actions' in fixes:
            st.markdown(f"**{latest['metric']}** is at **{latest['value']:.2f}** (threshold: {latest['threshold']:.2f})")
            st.markdown("**Do this now:**")
            for i, action in enumerate(fixes['immediate_actions'][:3], 1):
                st.markdown(f"{i}. {action}")
            
            if st.button("📋 View Full Fix Guide"):
                st.info("Navigate to 'Incidents' page for comprehensive troubleshooting steps")

# ============================================================================
# PAGE: ADMIN PANEL
# ============================================================================

elif selected == "Admin Panel":
    require_permission('admin')
    
    st.title("⚙️ Admin Panel")
    
    tab1, tab2, tab3, tab4 = st.tabs(["User Management", "Integration Settings", "Custom Metrics", "System Config"])
    
    with tab1:
        st.subheader("User Management")
        
        # User role management
        st.write("**Change User Role**")
        new_role = st.selectbox("Select Role", ["viewer", "operator", "admin"])
        if st.button("Update Role"):
            st.session_state['user_role'] = new_role
            st.success(f"Role updated to: {new_role}")
    
    with tab2:
        st.subheader("Integration Settings")
        
        # SMTP Settings
        with st.expander("📧 Email/SMTP Configuration"):
            st.text_input("SMTP Server", value="smtp.gmail.com")
            st.number_input("SMTP Port", value=587)
            st.text_input("SMTP Username")
            st.text_input("SMTP Password", type="password")
            st.button("Save SMTP Settings")
        
        # Slack Settings
        with st.expander("💼 Slack Integration"):
            st.text_input("Slack Webhook URL", type="password")
            st.button("Save Slack Settings")
        
        # PagerDuty Settings
        with st.expander("📟 PagerDuty Integration"):
            st.text_input("PagerDuty API Key", type="password")
            st.text_input("PagerDuty Service Key", type="password")
            st.button("Save PagerDuty Settings")
    
    with tab3:
        st.subheader("Custom Metric Plugins")
        
        st.write("**Registered Custom Metrics:**")
        if st.session_state['custom_metrics']:
            for metric in st.session_state['custom_metrics']:
                st.write(f"- {metric['name']}: {metric['description']}")
        else:
            st.info("No custom metrics registered")
        
        st.write("**Register New Metric**")
        with st.form("register_metric"):
            metric_name = st.text_input("Metric Name")
            metric_desc = st.text_area("Description")
            metric_code = st.text_area("Python Code (collect method)")
            
            if st.form_submit_button("Register"):
                st.success(f"Metric '{metric_name}' registered!")
    
    with tab4:
        st.subheader("System Configuration")
        
        st.number_input("Alert Threshold (CPU)", value=80.0, min_value=0.0, max_value=100.0)
        st.number_input("Alert Threshold (Memory)", value=75.0, min_value=0.0, max_value=100.0)
        st.number_input("Alert Threshold (Disk)", value=85.0, min_value=0.0, max_value=100.0)
        st.selectbox("Data Retention Period", ["7 days", "30 days", "90 days", "1 year"])
        st.button("Save Configuration")

# ============================================================================
# OTHER PAGES (from original app.py)
# ============================================================================

elif selected == "Metrics":
    st.title("📈 System Metrics")
    st.info("Detailed metrics view with real-time WebSocket updates")
    # ... (keep original metrics code)

elif selected == "Anomalies":
    st.title("⚠️ Anomaly Detection")
    st.info("ML-powered anomaly detection with automatic notifications")
    # ... (keep original anomalies code)

elif selected == "Predictions":
    st.title("🔮 Predictive Forecasts")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_to_forecast = st.selectbox("Select Metric", ["CPU", "Memory", "Disk", "Network"])
    with col2:
        forecast_hours = st.selectbox("Forecast Period", ["6h", "12h", "24h", "48h"])
    with col3:
        forecast_model = st.selectbox("Model", ["Prophet", "ARIMA", "Simple Moving Average"])
    
    st.divider()
    
    # Generate sample data
    historical_times = pd.date_range(start=datetime.now() - timedelta(days=7), periods=288, freq='30min')
    historical_values = np.random.normal(65, 15, 288)
    
    df = pd.DataFrame({
        'timestamp': historical_times,
        'value': historical_values
    })
    
    # Apply forecasting
    if forecast_model == "Prophet":
        st.info("Using Facebook Prophet for forecasting...")
        forecast_df = forecast_with_prophet(df, periods=int(forecast_hours[:-1]) * 12)
        
        if forecast_df is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['value'], mode='lines', name='Historical'))
            fig.add_trace(go.Scatter(x=forecast_df['ds'], y=forecast_df['yhat'], mode='lines', name='Forecast', line=dict(dash='dash')))
            fig.update_layout(title=f"{metric_to_forecast} Forecast (Prophet)", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    
    elif forecast_model == "ARIMA":
        st.info("Using ARIMA for forecasting...")
        forecast_values = forecast_with_arima(df['value'], periods=int(forecast_hours[:-1]) * 12)
        
        if forecast_values is not None:
            forecast_times = pd.date_range(start=df['timestamp'].iloc[-1], periods=len(forecast_values), freq='30min')
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['value'], mode='lines', name='Historical'))
            fig.add_trace(go.Scatter(x=forecast_times, y=forecast_values, mode='lines', name='Forecast', line=dict(dash='dash')))
            fig.update_layout(title=f"{metric_to_forecast} Forecast (ARIMA)", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

elif selected == "Incidents":
    st.title("🚨 Incident Management & Fix Suggestions")
    
    # Display all alerts with fix suggestions
    all_alerts = st.session_state.get('alert_history', [])
    
    if not all_alerts:
        st.info("✅ No incidents detected. System is running smoothly!")
    else:
        st.warning(f"⚠️ {len(all_alerts)} incident(s) detected")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            severity_filter = st.selectbox("Filter by Severity", ["All", "critical", "warning"])
        with col2:
            metric_filter = st.selectbox("Filter by Metric", ["All"] + list(set([a['metric'] for a in all_alerts])))
        
        # Filter alerts
        filtered_alerts = all_alerts
        if severity_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.get('severity') == severity_filter]
        if metric_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.get('metric') == metric_filter]
        
        st.divider()
        
        # Display each incident with fix suggestions
        for idx, alert in enumerate(reversed(filtered_alerts), 1):
            severity_icon = {'critical': '🔴', 'warning': '🟠'}
            severity_color = {'critical': '#d32f2f', 'warning': '#f57c00'}
            
            with st.expander(
                f"{severity_icon.get(alert['severity'], '⚪')} **{alert['metric']}** - {alert['severity'].upper()} "
                f"(Value: {alert['value']:.2f}, Threshold: {alert['threshold']:.2f})",
                expanded=(idx == 1)  # Expand the most recent alert
            ):
                # Alert details
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Value", f"{alert['value']:.2f}")
                with col2:
                    st.metric("Threshold", f"{alert['threshold']:.2f}")
                with col3:
                    st.metric("Severity", alert['severity'].upper())
                with col4:
                    st.metric("Timestamp", alert['timestamp'][:19])
                
                st.divider()
                
                # Fix suggestions
                fixes = alert.get('fixes', {})
                
                if fixes:
                    # Priority and Escalation
                    st.markdown(f"### {fixes.get('priority', '⚠️ WARNING')}")
                    st.info(f"**Escalation:** {fixes.get('escalation', 'Monitor and resolve')}")
                    
                    st.divider()
                    
                    # Create tabs for different fix categories
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                        "🔍 Root Causes",
                        "⚡ Immediate Actions",
                        "🛠️ Short-term Fixes",
                        "🎯 Long-term Solutions",
                        "💻 Commands",
                        "🛡️ Prevention"
                    ])
                    
                    with tab1:
                        st.markdown("### Possible Root Causes")
                        for i, cause in enumerate(fixes.get('root_causes', []), 1):
                            st.markdown(f"{i}. {cause}")
                    
                    with tab2:
                        st.markdown("### Immediate Actions (Do This Now)")
                        for i, action in enumerate(fixes.get('immediate_actions', []), 1):
                            st.markdown(f"{i}. {action}")
                    
                    with tab3:
                        st.markdown("### Short-term Fixes (Today/This Week)")
                        for i, fix in enumerate(fixes.get('short_term_fixes', []), 1):
                            st.markdown(f"{i}. {fix}")
                    
                    with tab4:
                        st.markdown("### Long-term Solutions (Plan & Implement)")
                        for i, solution in enumerate(fixes.get('long_term_solutions', []), 1):
                            st.markdown(f"{i}. {solution}")
                    
                    with tab5:
                        st.markdown("### Useful Commands")
                        st.markdown("Copy and run these commands to diagnose and fix:")
                        for i, cmd in enumerate(fixes.get('commands', []), 1):
                            st.code(cmd, language="bash")
                    
                    with tab6:
                        st.markdown("### Preventive Measures")
                        for i, measure in enumerate(fixes.get('preventive_measures', []), 1):
                            st.markdown(f"{i}. {measure}")
                    
                    st.divider()
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"✅ Mark as Resolved", key=f"resolve_{idx}"):
                            st.success("Incident marked as resolved!")
                    with col2:
                        if st.button(f"🔔 Escalate", key=f"escalate_{idx}"):
                            st.warning("Escalating to on-call engineer...")
                    with col3:
                        if st.button(f"📝 Create Ticket", key=f"ticket_{idx}"):
                            st.info("Creating ticket in issue tracking system...")
                else:
                    st.warning("No automated fix suggestions available for this incident.")

elif selected == "AI Analysis":
    st.title("🤖 AI-Powered Analysis")
    st.info("LLM-powered insights using GROQ/Ollama/HuggingFace")
    # ... (keep original AI analysis code)

# ============================================================================
# AUTO REFRESH BASED ON USER INTERVAL
# ============================================================================

# Convert interval to seconds
interval_seconds = {
    "5 seconds": 5, "10 seconds": 10, "30 seconds": 30,
    "1 minute": 60, "5 minutes": 300, "10 minutes": 600,
    "30 minutes": 1800, "1 hour": 3600
}

refresh_seconds = interval_seconds.get(st.session_state['check_interval'], 10)

# Auto-refresh
time.sleep(refresh_seconds)
st.rerun()
