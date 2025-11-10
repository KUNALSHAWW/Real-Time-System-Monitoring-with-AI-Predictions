"""
Real-Time System Monitoring Dashboard
Built with Streamlit for real-time visualization and incident management
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
from typing import Dict, Any, List
from collections import deque

# Import custom metrics fetcher
try:
    from metrics_fetcher import (
        MetricsFetcher, 
        fetch_and_cache_metrics, 
        get_latest_metrics,
        get_buffered_metrics_as_list
    )
    METRICS_MODULE_AVAILABLE = True
except ImportError:
    METRICS_MODULE_AVAILABLE = False
    print("Warning: metrics_fetcher module not available")

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="System Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Backend API configuration
API_BASE_URL = "http://localhost:8000"

# Initialize MetricsFetcher
if METRICS_MODULE_AVAILABLE:
    @st.cache_resource
    def get_fetcher():
        return MetricsFetcher(API_BASE_URL)
    
    fetcher = get_fetcher()
else:
    fetcher = None

# Initialize session state for metrics history
if 'metrics_history' not in st.session_state:
    st.session_state['metrics_history'] = deque(maxlen=100)
if 'backend_connected' not in st.session_state:
    st.session_state['backend_connected'] = False

# ============================================================================
# HELPER FUNCTIONS - METRICS
# ============================================================================

def check_backend_connection() -> bool:
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_realtime_metrics() -> Dict[str, Any]:
    """Get latest metrics from backend or use fallback"""
    if METRICS_MODULE_AVAILABLE and fetcher:
        try:
            metrics = fetch_and_cache_metrics(fetcher)
            # Also store in session state
            st.session_state['metrics_history'].append(metrics)
            st.session_state['backend_connected'] = True
            return metrics
        except Exception as e:
            st.session_state['backend_connected'] = False
            # Don't show error, just use fallback
    
    # Fallback to simulated data
    st.session_state['backend_connected'] = False
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
        metrics_list = get_buffered_metrics_as_list()
    else:
        metrics_list = list(st.session_state['metrics_history'])
    
    if len(metrics_list) == 0:
        # Return dummy data
        times = pd.date_range(start=datetime.now() - timedelta(minutes=10), periods=20, freq='30s')
        return pd.DataFrame({
            'timestamp': times,
            'cpu_percent': np.random.normal(65, 15, 20).clip(0, 100),
            'memory_percent': np.random.normal(55, 12, 20).clip(0, 100),
            'disk_percent': np.random.normal(72, 5, 20).clip(0, 100)
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(metrics_list)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

with st.sidebar:
    st.image("https://via.placeholder.com/250x50?text=System+Monitor", use_column_width=True)
    
    # Connection status - check actual backend connection
    backend_alive = check_backend_connection()
    
    if backend_alive and st.session_state.get('backend_connected', False):
        st.success("🟢 Connected to Backend")
    elif backend_alive:
        st.info("🟡 Backend Available (fetching...)")
    elif METRICS_MODULE_AVAILABLE:
        st.warning("� Backend Offline (using demo data)")
    else:
        st.error("� Demo Mode (No backend)")
    
    # Show backend URL
    with st.expander("Backend Info"):
        st.code(f"API: {API_BASE_URL}")
        if st.button("Test Connection"):
            if check_backend_connection():
                st.success("✅ Backend is reachable!")
            else:
                st.error("❌ Cannot reach backend")
    
    selected = option_menu(
        menu_title="Navigation",
        options=["Dashboard", "Metrics", "Anomalies", "Predictions", "Incidents", "AI Analysis"],
        icons=["speedometer2", "graph-up", "exclamation-triangle", "crystal-ball", "list-check", "robot"],
        menu_icon="cast",
        default_index=0
    )
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
    
    if auto_refresh:
        st.session_state['refresh'] = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_metric_card(col, title: str, value: str, delta: str = None, icon: str = "📊"):
    """Create metric card"""
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


def create_gauge_chart(value: float, max_value: float, title: str, unit: str = "%"):
    """Create gauge chart"""
    fig = go.Figure(data=[go.Gauge(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        delta={'reference': max_value * 0.8},
        gauge={
            'axis': {'range': [0, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    )])
    
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    return fig


# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

if selected == "Dashboard":
    st.title("📊 Real-Time System Monitoring Dashboard")
    
    # Get real-time metrics
    metrics = get_realtime_metrics()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    create_metric_card(
        col1, 
        "CPU Usage", 
        f"{metrics.get('cpu_percent', 0):.1f}%", 
        "+5%", 
        "⚙️"
    )
    create_metric_card(
        col2, 
        "Memory", 
        f"{metrics.get('memory_percent', 0):.1f}%", 
        "-2%", 
        "💾"
    )
    create_metric_card(
        col3, 
        "Disk", 
        f"{metrics.get('disk_percent', 0):.1f}%", 
        "+1%", 
        "💿"
    )
    
    # Calculate network speed (convert bytes to Mbps)
    network_sent_mb = metrics.get('network_sent', 0) / (1024 * 1024)
    create_metric_card(
        col4, 
        "Network (Sent)", 
        f"{network_sent_mb:.1f} MB", 
        "+12%", 
        "🌐"
    )
    
    st.divider()
    
    # System overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CPU Utilization Over Time (Real-time)")
        
        # Get historical data from WebSocket
        df_history = get_metrics_history()
        
        if not df_history.empty and 'cpu_percent' in df_history.columns:
            fig = create_line_chart(df_history, "CPU %", "timestamp", "cpu_percent")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for real-time data...")
    
    with col2:
        st.subheader("Memory & Disk Usage (Real-time)")
        
        df_history = get_metrics_history()
        
        if not df_history.empty:
            fig = go.Figure()
            
            if 'memory_percent' in df_history.columns:
                fig.add_trace(go.Scatter(
                    x=df_history['timestamp'],
                    y=df_history['memory_percent'],
                    mode='lines',
                    name='Memory',
                    line=dict(color='blue')
                ))
            
            if 'disk_percent' in df_history.columns:
                fig.add_trace(go.Scatter(
                    x=df_history['timestamp'],
                    y=df_history['disk_percent'],
                    mode='lines',
                    name='Disk',
                    line=dict(color='green')
                ))
            
            fig.update_layout(
                title="Memory & Disk %",
                template="plotly_dark",
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for real-time data...")
    
    st.divider()
    
    # Recent activities
    st.subheader("📋 Recent Activities")
    
    activities = [
        {"time": "10:45:23", "event": "High CPU detected on server-01", "severity": "🟠 Medium"},
        {"time": "10:42:15", "event": "Memory usage spike on server-02", "severity": "🟡 Low"},
        {"time": "10:39:47", "event": "Disk usage exceeded threshold", "severity": "🔴 Critical"},
        {"time": "10:35:12", "event": "Network latency increased", "severity": "🟡 Low"},
    ]
    
    for activity in activities:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.caption(activity["time"])
        with col2:
            st.write(activity["event"])
        with col3:
            st.caption(activity["severity"])


# ============================================================================
# PAGE: METRICS
# ============================================================================

elif selected == "Metrics":
    st.title("📈 System Metrics")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        metric_type = st.selectbox(
            "Select Metric",
            ["CPU", "Memory", "Disk", "Network", "Process"]
        )
    with col2:
        time_range = st.selectbox("Time Range", ["1h", "6h", "24h", "7d"])
    
    st.divider()
    
    # Generate sample metrics
    times = pd.date_range(start='2024-11-09', periods=288, freq='5min')
    
    if metric_type == "CPU":
        data = pd.DataFrame({
            'timestamp': times,
            'value': np.random.normal(65, 15, 288).clip(0, 100),
            'host': np.random.choice(['server-01', 'server-02', 'server-03'], 288)
        })
        
        fig = px.line(data, x='timestamp', y='value', color='host', title="CPU Utilization (%)")
        
    elif metric_type == "Memory":
        data = pd.DataFrame({
            'timestamp': times,
            'value': np.random.normal(55, 12, 288).clip(0, 100),
            'host': np.random.choice(['server-01', 'server-02', 'server-03'], 288)
        })
        
        fig = px.line(data, x='timestamp', y='value', color='host', title="Memory Utilization (%)")
    
    fig.update_layout(height=500, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics table
    st.subheader("Detailed Metrics")
    
    metrics_df = pd.DataFrame({
        'Timestamp': pd.date_range(start=datetime.now() - timedelta(hours=1), periods=12, freq='5min'),
        'Host': ['server-01'] * 12,
        'CPU (%)': np.random.uniform(50, 80, 12).round(2),
        'Memory (%)': np.random.uniform(40, 70, 12).round(2),
        'Disk (%)': np.random.uniform(60, 85, 12).round(2),
        'Network (Mbps)': np.random.uniform(100, 500, 12).round(2)
    })
    
    st.dataframe(metrics_df, use_container_width=True)


# ============================================================================
# PAGE: ANOMALIES
# ============================================================================

elif selected == "Anomalies":
    st.title("⚠️ Anomaly Detection")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Anomalies", "47", "-3")
    with col2:
        st.metric("Critical", "2", "+1")
    with col3:
        st.metric("Warning", "8", "-2")
    
    st.divider()
    
    # Anomaly timeline
    st.subheader("Anomaly Timeline")
    
    anomalies = pd.DataFrame({
        'Timestamp': pd.date_range(start=datetime.now() - timedelta(hours=24), periods=47, freq='30min'),
        'Metric': np.random.choice(['CPU', 'Memory', 'Disk', 'Network'], 47),
        'Severity': np.random.choice(['Low', 'Medium', 'High', 'Critical'], 47),
        'Value': np.random.uniform(50, 100, 47).round(2),
        'Score': np.random.uniform(0.5, 1.0, 47).round(2)
    })
    
    fig = px.scatter(
        anomalies,
        x='Timestamp',
        y='Value',
        color='Severity',
        size='Score',
        hover_data=['Metric'],
        title="Anomalies Over Time",
        color_discrete_map={'Low': 'yellow', 'Medium': 'orange', 'High': 'red', 'Critical': 'darkred'}
    )
    
    fig.update_layout(height=400, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly details
    st.subheader("Recent Anomalies")
    st.dataframe(anomalies.sort_values('Timestamp', ascending=False).head(10), use_container_width=True)


# ============================================================================
# PAGE: PREDICTIONS
# ============================================================================

elif selected == "Predictions":
    st.title("🔮 Predictive Forecasts")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        metric_to_forecast = st.selectbox("Select Metric to Forecast", ["CPU", "Memory", "Disk", "Network"])
    with col2:
        forecast_hours = st.selectbox("Forecast Period", ["6h", "12h", "24h"])
    
    st.divider()
    
    # Generate forecast
    historical_times = pd.date_range(start='2024-11-09', periods=288, freq='5min')
    forecast_times = pd.date_range(start='2024-11-10 12:00', periods=int(forecast_hours.split('h')[0]) * 12, freq='5min')
    
    historical_values = np.random.normal(65, 15, 288)
    trend = np.linspace(0, 10, len(forecast_times))
    forecast_values = historical_values[-1] + trend + np.random.normal(0, 5, len(forecast_times))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=historical_times, y=historical_values,
        mode='lines',
        name='Historical',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_times, y=forecast_values,
        mode='lines',
        name='Forecast',
        line=dict(color='red', dash='dash')
    ))
    
    # Add confidence interval
    fig.add_trace(go.Scatter(
        x=forecast_times.tolist() + forecast_times[::-1].tolist(),
        y=(forecast_values + 10).tolist() + (forecast_values - 10)[::-1].tolist(),
        fill='toself',
        name='Confidence Interval',
        fillcolor='rgba(255,0,0,0.1)',
        line=dict(color='rgba(255,255,255,0)')
    ))
    
    fig.update_layout(
        title=f"{metric_to_forecast} Forecast ({forecast_hours})",
        xaxis_title="Time",
        yaxis_title="Value",
        height=500,
        template="plotly_dark",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Alert predictions
    st.subheader("Predicted Alerts")
    
    predictions = [
        {"time": "2024-11-10 14:30", "alert": "CPU likely to exceed 85%", "probability": "78%", "severity": "🟠"},
        {"time": "2024-11-10 16:00", "alert": "Memory usage spike expected", "probability": "65%", "severity": "🟡"},
        {"time": "2024-11-10 18:30", "alert": "Disk usage approaching limit", "probability": "45%", "severity": "🟡"},
    ]
    
    for pred in predictions:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        with col1:
            st.write(pred["time"])
        with col2:
            st.write(pred["alert"])
        with col3:
            st.write(pred["probability"])
        with col4:
            st.write(pred["severity"])


# ============================================================================
# PAGE: INCIDENTS
# ============================================================================

elif selected == "Incidents":
    st.title("🚨 Incident Management")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Open", "3")
    with col2:
        st.metric("Investigating", "1")
    with col3:
        st.metric("Resolved Today", "5")
    with col4:
        st.metric("MTTR (avg)", "45 min")
    
    st.divider()
    
    # Create incident tab
    tab1, tab2 = st.tabs(["Active Incidents", "Create Incident"])
    
    with tab1:
        st.subheader("Active Incidents")
        
        incidents = [
            {
                "ID": "INC-001",
                "Title": "High CPU on server-01",
                "Status": "🔴 Open",
                "Severity": "Critical",
                "Created": "10:45",
                "Assigned": "John Doe"
            },
            {
                "ID": "INC-002",
                "Title": "Memory leak detected",
                "Status": "🟠 Investigating",
                "Severity": "High",
                "Created": "09:20",
                "Assigned": "Jane Smith"
            },
        ]
        
        incidents_df = pd.DataFrame(incidents)
        st.dataframe(incidents_df, use_container_width=True)
    
    with tab2:
        st.subheader("Create New Incident")
        
        with st.form("new_incident_form"):
            title = st.text_input("Incident Title")
            description = st.text_area("Description")
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
            assignee = st.selectbox("Assign To", ["John Doe", "Jane Smith", "Mike Johnson"])
            
            if st.form_submit_button("Create Incident"):
                st.success("✅ Incident created successfully!")


# ============================================================================
# PAGE: AI ANALYSIS
# ============================================================================

elif selected == "AI Analysis":
    st.title("🤖 AI-Powered Analysis")
    
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Metric Analysis", "Anomaly Explanation", "Incident Summary", "System Health Report"]
    )
    
    st.divider()
    
    if analysis_type == "Metric Analysis":
        st.subheader("Analyze System Metrics with AI")
        
        query = st.text_area(
            "Enter your analysis query",
            placeholder="e.g., Why is CPU usage high? What could be causing the spike?"
        )
        
        model = st.radio("AI Model", ["GROQ (Llama 2)", "Local Ollama", "Hugging Face"])
        
        if st.button("🔍 Analyze"):
            with st.spinner("Analyzing..."):
                st.info(
                    "🤖 AI Analysis Result:\n\n"
                    "Based on the recent metrics, the CPU spike appears to be caused by:\n\n"
                    "1. **Background Jobs**: Scheduled maintenance tasks running\n"
                    "2. **Database Queries**: High number of concurrent queries\n"
                    "3. **Memory Pressure**: Increased swap usage detected\n\n"
                    "**Recommendations**:\n"
                    "- Reschedule maintenance tasks to off-peak hours\n"
                    "- Optimize slow-running queries\n"
                    "- Consider increasing server capacity"
                )
    
    elif analysis_type == "Anomaly Explanation":
        st.subheader("Explain Detected Anomalies")
        
        selected_anomaly = st.selectbox(
            "Select Anomaly",
            ["Memory spike at 14:30", "Network latency at 15:45", "Disk usage jump at 16:00"]
        )
        
        if st.button("📖 Explain Anomaly"):
            st.info(
                f"**Analysis of: {selected_anomaly}**\n\n"
                "This anomaly appears to be caused by:\n\n"
                "- Temporary resource usage spike\n"
                "- Possible data processing task\n"
                "- No correlation with other system failures"
            )


# ============================================================================
# AUTO REFRESH
# ============================================================================

if auto_refresh:
    # Use streamlit-autorefresh if available
    try:
        from streamlit_autorefresh import st_autorefresh
        count = st_autorefresh(interval=refresh_interval * 1000, key="metrics_refresh")
    except ImportError:
        # Fallback to time.sleep and rerun
        import time
        time.sleep(refresh_interval)
        st.rerun()
