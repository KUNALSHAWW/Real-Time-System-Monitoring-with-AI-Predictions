"""
Real-Time System Monitoring Dashboard
Production-ready Streamlit app for Hugging Face Spaces deployment
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
import os
from typing import Dict, Any, List
from collections import deque

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

# Backend API configuration - Use environment variable for Hugging Face Spaces
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

# Initialize session state
if 'metrics_history' not in st.session_state:
    st.session_state['metrics_history'] = deque(maxlen=100)
if 'backend_connected' not in st.session_state:
    st.session_state['backend_connected'] = False
if 'last_error' not in st.session_state:
    st.session_state['last_error'] = None
if 'host_info' not in st.session_state:
    st.session_state['host_info'] = None

# ============================================================================
# HELPER FUNCTIONS - API CALLS
# ============================================================================

def check_backend_connection() -> bool:
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        st.session_state['last_error'] = str(e)
        return False


def fetch_current_metrics() -> Dict[str, Any]:
    """Fetch current metrics from backend API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/metrics/current", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state['backend_connected'] = True
            st.session_state['last_error'] = None
            
            # Store host info
            if 'host_info' in data:
                st.session_state['host_info'] = data['host_info']
            
            # Add to history
            st.session_state['metrics_history'].append(data)
            return data
        else:
            st.session_state['backend_connected'] = False
            st.session_state['last_error'] = f"API returned status {response.status_code}"
            return None
            
    except requests.exceptions.ConnectionError:
        st.session_state['backend_connected'] = False
        st.session_state['last_error'] = "Connection Error: Cannot reach backend server"
        return None
    except requests.exceptions.Timeout:
        st.session_state['backend_connected'] = False
        st.session_state['last_error'] = "Timeout: Backend server not responding"
        return None
    except Exception as e:
        st.session_state['backend_connected'] = False
        st.session_state['last_error'] = f"Error: {str(e)}"
        return None


def fetch_incidents() -> List[Dict[str, Any]]:
    """Fetch incidents from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/incidents/list", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def fetch_incident_stats() -> Dict[str, Any]:
    """Fetch incident statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/incidents/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def fetch_predictions(metric: str, hours: int = 1) -> Dict[str, Any]:
    """Fetch predictions for a metric"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/predictions/forecast/{metric}?hours={hours}", timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def fetch_anomaly_risk() -> Dict[str, Any]:
    """Fetch anomaly risk assessment"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/predictions/anomaly-risk", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def analyze_with_ai(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send analysis request to AI endpoint"""
    try:
        payload = {
            "query": query,
            "context": context or {},
            "include_current_metrics": True
        }
        response = requests.post(
            f"{API_BASE_URL}/api/ai/analyze",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Analysis failed")}
    except Exception as e:
        return {"error": str(e)}


def send_email_report(email: str, include_ai: bool = True, message: str = "") -> Dict[str, Any]:
    """Send email report"""
    try:
        payload = {
            "recipient_email": email,
            "subject": "System Monitoring Report",
            "include_ai_analysis": include_ai,
            "custom_message": message
        }
        response = requests.post(
            f"{API_BASE_URL}/api/reports/send-report",
            json=payload,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def create_incident(title: str, description: str, severity: str) -> Dict[str, Any]:
    """Create a new incident"""
    try:
        payload = {
            "title": title,
            "description": description,
            "severity": severity
        }
        response = requests.post(
            f"{API_BASE_URL}/api/incidents/create",
            json=payload,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================

def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"


def get_status_color(value: float) -> str:
    """Get status color based on value"""
    if value >= 90:
        return "🔴"
    elif value >= 70:
        return "🟡"
    else:
        return "🟢"


def create_gauge_chart(value: float, title: str, max_val: float = 100):
    """Create a gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, max_val], 'tickwidth': 1},
            'bar': {'color': "#3498db"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#2ecc71'},
                {'range': [50, 70], 'color': '#f1c40f'},
                {'range': [70, 90], 'color': '#e67e22'},
                {'range': [90, 100], 'color': '#e74c3c'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("📊 System Monitor")
    
    # Connection status
    backend_alive = check_backend_connection()
    
    if backend_alive and st.session_state.get('backend_connected', False):
        st.success("🟢 Connected to Backend")
        if st.session_state.get('host_info'):
            hi = st.session_state['host_info']
            st.caption(f"📍 {hi.get('hostname', 'Unknown')}")
            st.caption(f"🐧 {hi.get('os', 'Unknown')} {hi.get('os_version', '')}")
    elif backend_alive:
        st.info("🟡 Backend Available")
    else:
        st.error("🔴 Backend Offline")
        if st.session_state.get('last_error'):
            st.caption(f"⚠️ {st.session_state['last_error']}")
    
    # Backend info
    with st.expander("🔧 Configuration"):
        st.code(f"API: {API_BASE_URL}")
        if st.button("🔄 Test Connection"):
            if check_backend_connection():
                st.success("✅ Connection OK!")
            else:
                st.error("❌ Connection Failed")
    
    st.divider()
    
    # Navigation
    selected = option_menu(
        menu_title="Navigation",
        options=["Dashboard", "Predictions", "Incidents", "AI Analysis", "Reports"],
        icons=["speedometer2", "graph-up-arrow", "exclamation-triangle", "robot", "envelope"],
        menu_icon="cast",
        default_index=0
    )
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Refresh (seconds)", 5, 60, 10)


# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

if selected == "Dashboard":
    st.title("📊 Real-Time System Monitoring")
    
    # Fetch current metrics
    metrics = fetch_current_metrics()
    
    if metrics is None:
        st.error("⚠️ Cannot connect to backend server")
        st.info(f"""
        **Connection Error**: Unable to reach the backend at `{API_BASE_URL}`
        
        Possible solutions:
        1. Ensure the backend is running
        2. Check the `BACKEND_URL` environment variable
        3. Verify network connectivity
        """)
        st.stop()
    
    # Host Information Banner
    if st.session_state.get('host_info'):
        hi = st.session_state['host_info']
        with st.container():
            st.info(f"🖥️ **Monitoring:** {hi.get('hostname', 'Container')} | **OS:** {hi.get('os', 'Linux')} {hi.get('os_version', '')} | **CPU Cores:** {hi.get('cpu_count_logical', 'N/A')}")
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu = metrics.get('cpu_percent', 0)
        st.metric(
            label=f"{get_status_color(cpu)} CPU Usage",
            value=f"{cpu:.1f}%"
        )
    
    with col2:
        mem = metrics.get('memory_percent', 0)
        st.metric(
            label=f"{get_status_color(mem)} Memory",
            value=f"{mem:.1f}%",
            delta=f"{format_bytes(metrics.get('memory_used', 0))} used"
        )
    
    with col3:
        disk = metrics.get('disk_percent', 0)
        st.metric(
            label=f"{get_status_color(disk)} Disk",
            value=f"{disk:.1f}%",
            delta=f"{format_bytes(metrics.get('disk_free', 0))} free"
        )
    
    with col4:
        processes = metrics.get('process_count', 0)
        st.metric(
            label="⚙️ Processes",
            value=str(processes)
        )
    
    st.divider()
    
    # Gauge Charts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = create_gauge_chart(metrics.get('cpu_percent', 0), "CPU %")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = create_gauge_chart(metrics.get('memory_percent', 0), "Memory %")
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = create_gauge_chart(metrics.get('disk_percent', 0), "Disk %")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Historical Charts
    col1, col2 = st.columns(2)
    
    history = list(st.session_state['metrics_history'])
    
    if len(history) > 1:
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        with col1:
            st.subheader("📈 CPU & Memory Over Time")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['cpu_percent'], name='CPU %', line=dict(color='#3498db')))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['memory_percent'], name='Memory %', line=dict(color='#e74c3c')))
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0), hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💾 Disk Usage")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['disk_percent'], name='Disk %', fill='tozeroy', line=dict(color='#27ae60')))
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Collecting metrics data... Charts will appear after a few data points.")
    
    # Network Info
    st.subheader("🌐 Network I/O")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("⬆️ Bytes Sent", format_bytes(metrics.get('network_sent', 0)))
    with col2:
        st.metric("⬇️ Bytes Received", format_bytes(metrics.get('network_recv', 0)))


# ============================================================================
# PAGE: PREDICTIONS
# ============================================================================

elif selected == "Predictions":
    st.title("🔮 Real-Time Predictive Forecasts")
    
    # Fetch current metrics first to show live status
    current_metrics = fetch_current_metrics()
    
    if current_metrics:
        # Show LIVE current values at the top
        st.subheader("📊 Current System Status (LIVE)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            cpu_val = current_metrics.get('cpu_percent', 0)
            st.metric("🔥 CPU", f"{cpu_val:.1f}%", 
                      delta=f"{get_status_color(cpu_val)} {'Critical' if cpu_val > 90 else 'High' if cpu_val > 70 else 'Normal'}")
        with col2:
            mem_val = current_metrics.get('memory_percent', 0)
            st.metric("💾 Memory", f"{mem_val:.1f}%",
                      delta=f"{get_status_color(mem_val)} {'Critical' if mem_val > 90 else 'High' if mem_val > 70 else 'Normal'}")
        with col3:
            disk_val = current_metrics.get('disk_percent', 0)
            st.metric("💿 Disk", f"{disk_val:.1f}%",
                      delta=f"{get_status_color(disk_val)} {'Critical' if disk_val > 90 else 'High' if disk_val > 70 else 'Normal'}")
        with col4:
            st.metric("⏱️ Updated", datetime.now().strftime("%H:%M:%S"))
        
        st.divider()
    
    # Selection controls
    col1, col2 = st.columns([2, 1])
    with col1:
        metric_choice = st.selectbox("Select Metric", ["cpu", "memory", "disk"], key="pred_metric")
    with col2:
        forecast_hours = st.selectbox("Forecast Period (hours)", [1, 2, 6, 12], key="pred_hours")
    
    # AUTO-LOAD predictions (no button required)
    st.subheader(f"📈 {metric_choice.upper()} Forecast - Next {forecast_hours} Hour(s)")
    
    with st.spinner("Loading real-time forecast..."):
        predictions = fetch_predictions(metric_choice, forecast_hours)
    
    if predictions and predictions.get('predictions'):
        data_points = predictions.get('data_points_used', 0)
        
        # Status indicator
        if data_points >= 10:
            st.success(f"✅ Forecast ready • Using {data_points} real data points • Updated: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning(f"⏳ Limited data ({data_points} points) - forecast accuracy improves over time")
        
        # Show explanation
        if 'explanation' in predictions:
            st.markdown(predictions['explanation'])
        
        # Build forecast chart with CURRENT + PREDICTED data
        pred_df = pd.DataFrame(predictions['predictions'])
        pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
        
        fig = go.Figure()
        
        # Add current value marker
        current_val = predictions.get('current_value', 0)
        now_time = datetime.utcnow()
        
        fig.add_trace(go.Scatter(
            x=[now_time],
            y=[current_val],
            mode='markers',
            name='Current (LIVE)',
            marker=dict(color='#e74c3c', size=15, symbol='diamond'),
            hovertemplate=f"NOW<br>Value: {current_val:.1f}%<extra></extra>"
        ))
        
        # Add forecast line
        fig.add_trace(go.Scatter(
            x=pred_df['timestamp'],
            y=pred_df['predicted_value'],
            mode='lines+markers',
            name='Predicted',
            line=dict(color='#9b59b6', width=3, dash='dash'),
            marker=dict(size=6)
        ))
        
        # Add confidence bands
        upper = pred_df['predicted_value'] + (1 - pred_df['confidence']) * 10
        lower = pred_df['predicted_value'] - (1 - pred_df['confidence']) * 10
        lower = lower.clip(lower=0)  # Can't go below 0%
        upper = upper.clip(upper=100)  # Can't go above 100%
        
        fig.add_trace(go.Scatter(
            x=pred_df['timestamp'].tolist() + pred_df['timestamp'][::-1].tolist(),
            y=upper.tolist() + lower[::-1].tolist(),
            fill='toself',
            fillcolor='rgba(155, 89, 182, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Confidence Band',
            hoverinfo='skip'
        ))
        
        # Add warning threshold line
        fig.add_hline(y=70, line_dash="dot", line_color="orange", 
                      annotation_text="Warning (70%)", annotation_position="right")
        fig.add_hline(y=90, line_dash="dot", line_color="red", 
                      annotation_text="Critical (90%)", annotation_position="right")
        
        fig.update_layout(
            title=f"📊 {metric_choice.upper()} Usage: Current vs Forecast",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            yaxis=dict(range=[0, 105]),
            height=450,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📍 Current", f"{current_val:.1f}%")
        with col2:
            pred_max = max([p['predicted_value'] for p in predictions['predictions']])
            st.metric("📈 Predicted Max", f"{pred_max:.1f}%")
        with col3:
            pred_avg = sum([p['predicted_value'] for p in predictions['predictions']]) / len(predictions['predictions'])
            st.metric("📊 Predicted Avg", f"{pred_avg:.1f}%")
        with col4:
            prob = predictions.get('next_anomaly_probability', 0)
            risk_emoji = "🔴" if prob > 0.6 else "🟡" if prob > 0.3 else "🟢"
            st.metric(f"{risk_emoji} Anomaly Risk", f"{prob * 100:.0f}%")
    
    elif predictions and predictions.get('explanation'):
        st.info(predictions['explanation'])
    else:
        st.warning("⏳ Not enough historical data yet. The system collects metrics every 5 seconds - please wait a minute and refresh.")
    
    st.divider()
    
    # ============ ANOMALY RISK ASSESSMENT (AUTO-LOAD) ============
    st.subheader("⚠️ Real-Time Anomaly Risk Assessment")
    
    risk_data = fetch_anomaly_risk()
    
    if risk_data and risk_data.get('metrics_risk'):
        risk_level = risk_data.get('risk_level', 'unknown').upper()
        risk_color_map = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "UNKNOWN": "⚪"}
        risk_color = risk_color_map.get(risk_level, "⚪")
        
        # Overall risk display
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"### {risk_color} {risk_level} RISK")
            st.metric("Overall Probability", f"{risk_data.get('overall_probability', 0) * 100:.0f}%")
        with col2:
            if risk_data.get('top_risk_metric'):
                st.warning(f"⚠️ Highest risk: **{risk_data['top_risk_metric'].upper()}**")
        
        # Per-metric breakdown
        cols = st.columns(3)
        metrics_risk = risk_data.get('metrics_risk', {})
        for i, metric_name in enumerate(["cpu", "memory", "disk"]):
            if metric_name in metrics_risk:
                data = metrics_risk[metric_name]
                with cols[i]:
                    prob = data.get('probability', 0)
                    color = "🔴" if prob > 0.6 else "🟡" if prob > 0.3 else "🟢"
                    trend = data.get('trend', 'stable')
                    trend_icon = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
                    st.metric(
                        label=f"{color} {metric_name.upper()}",
                        value=f"{data.get('current', 0):.1f}%",
                        delta=f"{trend_icon} {trend.title()} • Risk: {prob * 100:.0f}%"
                    )
    elif risk_data and risk_data.get('message'):
        st.info(f"ℹ️ {risk_data.get('message')} ({risk_data.get('data_points', 0)} data points collected)")
    else:
        st.info("⏳ Collecting data for risk assessment... Please wait 30 seconds.")
    
    # Manual refresh button
    st.divider()
    if st.button("🔄 Refresh Predictions Now"):
        st.rerun()


# ============================================================================
# PAGE: INCIDENTS
# ============================================================================

elif selected == "Incidents":
    st.title("🚨 Incident Management")
    
    # Fetch stats
    stats = fetch_incident_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Open", stats.get('open', 0))
    with col2:
        st.metric("Investigating", stats.get('investigating', 0))
    with col3:
        st.metric("Resolved", stats.get('resolved', 0))
    with col4:
        st.metric("Auto-Generated", stats.get('auto_generated', 0))
    
    st.divider()
    
    tab1, tab2 = st.tabs(["📋 Active Incidents", "➕ Create Incident"])
    
    with tab1:
        incidents = fetch_incidents()
        
        if incidents:
            for inc in incidents[:10]:  # Show latest 10
                with st.expander(f"{inc.get('severity', 'medium').upper()} | {inc.get('title', 'Untitled')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID:** {inc.get('id')}")
                        st.write(f"**Status:** {inc.get('status')}")
                        st.write(f"**Auto-Generated:** {'Yes' if inc.get('auto_generated') else 'No'}")
                    with col2:
                        st.write(f"**Created:** {inc.get('created_at')}")
                        if inc.get('metric_type'):
                            st.write(f"**Metric:** {inc.get('metric_type')} = {inc.get('metric_value'):.1f}%")
                    st.write(f"**Description:** {inc.get('description')}")
        else:
            st.info("✅ No active incidents")
    
    with tab2:
        with st.form("create_incident"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            severity = st.selectbox("Severity", ["low", "medium", "high", "critical"])
            
            if st.form_submit_button("🚨 Create Incident"):
                if title and description:
                    result = create_incident(title, description, severity)
                    if 'error' not in result:
                        st.success(f"✅ Incident created: {result.get('id')}")
                    else:
                        st.error(f"❌ Failed: {result.get('error')}")
                else:
                    st.warning("Please fill in all fields")


# ============================================================================
# PAGE: AI ANALYSIS
# ============================================================================

elif selected == "AI Analysis":
    st.title("🤖 AI-Powered Analysis")
    
    st.markdown("""
    Ask questions about your system's performance and get AI-powered insights.
    The AI has access to real-time metrics from your container.
    """)
    
    # Quick Analysis Buttons
    st.subheader("🚀 Quick Analysis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 System Health Check"):
            with st.spinner("Analyzing system health..."):
                result = analyze_with_ai("Provide a comprehensive health check of the current system status.")
                if 'analysis' in result:
                    st.markdown(result['analysis'])
                    st.caption(f"Model: {result.get('model_used', 'N/A')}")
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    with col2:
        if st.button("⚠️ Risk Assessment"):
            with st.spinner("Assessing risks..."):
                result = analyze_with_ai("What are the potential risks and issues I should be aware of?")
                if 'analysis' in result:
                    st.markdown(result['analysis'])
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    with col3:
        if st.button("💡 Optimization Tips"):
            with st.spinner("Generating tips..."):
                result = analyze_with_ai("Provide optimization recommendations to improve system performance.")
                if 'analysis' in result:
                    st.markdown(result['analysis'])
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
    
    st.divider()
    
    # Custom Query
    st.subheader("💬 Custom Query")
    query = st.text_area(
        "Ask anything about your system",
        placeholder="e.g., Why is CPU usage high? What's consuming the most memory?"
    )
    
    if st.button("🔍 Analyze"):
        if query:
            with st.spinner("Analyzing with AI..."):
                result = analyze_with_ai(query)
                if 'analysis' in result:
                    st.markdown("### 🤖 AI Response")
                    st.markdown(result['analysis'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"Model: {result.get('model_used', 'N/A')}")
                    with col2:
                        st.caption(f"Metrics included: {'✅' if result.get('metrics_included') else '❌'}")
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a query")


# ============================================================================
# PAGE: REPORTS
# ============================================================================

elif selected == "Reports":
    st.title("📧 Email Reports")
    
    st.markdown("""
    Send detailed system monitoring reports via email.
    Reports include current metrics, AI analysis, and visual status indicators.
    """)
    
    # Check email configuration
    try:
        response = requests.get(f"{API_BASE_URL}/api/reports/email-config", timeout=5)
        config = response.json() if response.status_code == 200 else {}
    except:
        config = {}
    
    if config.get('email_configured'):
        st.success("✅ Email is configured")
    else:
        st.warning("⚠️ Email not configured. Set EMAIL_USER and EMAIL_PASS in backend secrets.")
    
    st.divider()
    
    with st.form("send_report"):
        recipient = st.text_input("Recipient Email", placeholder="user@example.com")
        include_ai = st.checkbox("Include AI Analysis", value=True)
        custom_message = st.text_area("Custom Message (optional)", placeholder="Add any notes...")
        
        if st.form_submit_button("📤 Send Report"):
            if recipient:
                with st.spinner("Sending report..."):
                    result = send_email_report(recipient, include_ai, custom_message)
                    
                    if result.get('success'):
                        st.success(f"✅ Report sent to {recipient}!")
                        st.balloons()
                    else:
                        error = result.get('error') or result.get('detail', {}).get('message', 'Unknown error')
                        st.error(f"❌ Failed to send: {error}")
            else:
                st.warning("Please enter a recipient email")


# ============================================================================
# AUTO REFRESH
# ============================================================================

if auto_refresh:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh")
    except ImportError:
        import time
        time.sleep(refresh_interval)
        st.rerun()
