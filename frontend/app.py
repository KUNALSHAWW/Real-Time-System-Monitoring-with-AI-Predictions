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
# SIDEBAR NAVIGATION
# ============================================================================

with st.sidebar:
    st.image("https://via.placeholder.com/250x50?text=System+Monitor", use_column_width=True)
    
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
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    create_metric_card(col1, "CPU Usage", "67%", "+5%", "⚙️")
    create_metric_card(col2, "Memory", "45%", "-2%", "💾")
    create_metric_card(col3, "Disk", "72%", "+1%", "💿")
    create_metric_card(col4, "Network", "234 Mbps", "+12%", "🌐")
    
    st.divider()
    
    # System overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CPU Utilization Over Time")
        
        # Generate sample data
        times = pd.date_range(start='2024-11-10 00:00', periods=100, freq='5min')
        cpu_data = pd.DataFrame({
            'time': times,
            'cpu': np.random.normal(65, 15, 100).clip(0, 100)
        })
        
        fig = create_line_chart(cpu_data, "CPU %", "time", "cpu")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("System Health")
        
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
    import time
    time.sleep(refresh_interval)
    st.rerun()
