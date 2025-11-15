"""
Streamlit Dashboard for Network Troubleshooting Bot
Real-time monitoring and visualization interface
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import requests
import time
from datetime import datetime, timedelta
import yaml
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import DatabaseManager, Device, TestResult, Alert, NetworkMetric
from modules import ping_host, traceroute_host, get_device_snmp_info
from ai import process_user_query

# Page configuration
st.set_page_config(
    page_title="Network Troubleshooting Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e2e6;
    }
    .success-metric {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    .warning-metric {
        background-color: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
    }
    .danger-metric {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database and configuration
@st.cache_resource
def init_database():
    db_manager = DatabaseManager()
    db_manager.create_tables()
    return db_manager

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_config():
    try:
        config_path = os.path.join("config", "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        st.error("Configuration file not found. Please ensure config/config.yaml exists.")
        return {}

# Initialize
db_manager = init_database()
config = load_config()

# Sidebar
st.sidebar.title("🌐 Network Bot Dashboard")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.selectbox(
    "Navigate to:",
    ["🏠 Overview", "🔍 Live Testing", "📊 Analytics", "🚨 Alerts", "💬 Chat Interface", "⚙️ Settings"]
)

st.sidebar.markdown("---")

# Auto-refresh option
auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# Main content based on navigation
if page == "🏠 Overview":
    st.title("🌐 Network Troubleshooting Dashboard")
    st.markdown("Real-time network monitoring and diagnostics")
    
    # Get recent data
    session = db_manager.get_session()
    try:
        # Recent test results
        recent_tests = session.query(TestResult).order_by(TestResult.timestamp.desc()).limit(100).all()
        
        # Recent alerts
        recent_alerts = session.query(Alert).order_by(Alert.created_at.desc()).limit(50).all()
        
        # Device count
        device_count = session.query(Device).count()
        
        # Active alerts
        active_alerts = session.query(Alert).filter(Alert.status == 'open').count()
        
    finally:
        session.close()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Devices",
            value=device_count,
            delta=None
        )
    
    with col2:
        success_rate = (len([t for t in recent_tests if t.status == 'success']) / len(recent_tests) * 100) if recent_tests else 0
        st.metric(
            label="Success Rate (24h)",
            value=f"{success_rate:.1f}%",
            delta=f"{'📈' if success_rate > 90 else '📉'}"
        )
    
    with col3:
        st.metric(
            label="Active Alerts",
            value=active_alerts,
            delta="🚨" if active_alerts > 0 else "✅"
        )
    
    with col4:
        avg_latency = sum([t.latency_ms for t in recent_tests if t.latency_ms]) / len([t for t in recent_tests if t.latency_ms]) if recent_tests else 0
        st.metric(
            label="Avg Latency",
            value=f"{avg_latency:.1f}ms",
            delta="🟢" if avg_latency < 50 else "🟡" if avg_latency < 100 else "🔴"
        )
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Test Results Over Time")
        if recent_tests:
            # Create DataFrame for plotting
            df_tests = pd.DataFrame([
                {
                    'timestamp': test.timestamp,
                    'test_type': test.test_type,
                    'status': test.status,
                    'latency_ms': test.latency_ms or 0
                }
                for test in recent_tests
            ])
            
            # Convert timestamp
            df_tests['timestamp'] = pd.to_datetime(df_tests['timestamp'], unit='s')
            
            # Plot test results timeline
            fig = px.scatter(
                df_tests, 
                x='timestamp', 
                y='latency_ms',
                color='status',
                symbol='test_type',
                title="Test Results Timeline",
                color_discrete_map={'success': 'green', 'failed': 'red', 'timeout': 'orange'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No test data available")
    
    with col2:
        st.subheader("🎯 Test Type Distribution")
        if recent_tests:
            test_counts = {}
            for test in recent_tests:
                test_counts[test.test_type] = test_counts.get(test.test_type, 0) + 1
            
            fig = px.pie(
                values=list(test_counts.values()),
                names=list(test_counts.keys()),
                title="Test Types (Last 100 Tests)"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No test data available")
    
    # Recent activity
    st.subheader("📋 Recent Activity")
    
    if recent_tests:
        # Display recent tests in a table
        recent_df = pd.DataFrame([
            {
                'Time': datetime.fromtimestamp(test.timestamp).strftime('%H:%M:%S'),
                'Type': test.test_type.upper(),
                'Target': test.target,
                'Status': '✅' if test.status == 'success' else '❌',
                'Latency (ms)': f"{test.latency_ms:.1f}" if test.latency_ms else "N/A",
                'Packet Loss (%)': f"{test.packet_loss:.1f}" if test.packet_loss else "N/A"
            }
            for test in recent_tests[:10]
        ])
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("No recent test data available")

elif page == "🔍 Live Testing":
    st.title("🔍 Live Network Testing")
    st.markdown("Perform real-time network diagnostics")
    
    # Test selection tabs
    test_tab1, test_tab2, test_tab3 = st.tabs(["🏓 Ping Test", "🛤️ Traceroute", "📊 SNMP Monitor"])
    
    with test_tab1:
        st.subheader("🏓 Ping Test")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            ping_target = st.text_input("Target (IP or hostname):", placeholder="8.8.8.8 or google.com")
        with col2:
            ping_count = st.number_input("Packet Count:", min_value=1, max_value=10, value=4)
        with col3:
            ping_timeout = st.number_input("Timeout (s):", min_value=1, max_value=30, value=5)
        
        if st.button("🚀 Run Ping Test", type="primary"):
            if ping_target:
                with st.spinner(f"Pinging {ping_target}..."):
                    try:
                        result = asyncio.run(ping_host(ping_target, ping_timeout, ping_count))
                        
                        if result.success:
                            st.success(f"✅ Ping to {ping_target} successful!")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Packets Sent", result.packets_sent)
                            with col2:
                                st.metric("Packets Received", result.packets_received)
                            with col3:
                                st.metric("Packet Loss", f"{result.packet_loss_percent:.1f}%")
                            with col4:
                                st.metric("Avg Latency", f"{result.avg_latency_ms:.2f}ms")
                            
                            # Latency details
                            if result.min_latency_ms and result.max_latency_ms:
                                st.info(f"🕐 Latency Range: {result.min_latency_ms:.2f}ms - {result.max_latency_ms:.2f}ms")
                        else:
                            st.error(f"❌ Ping to {ping_target} failed!")
                            if result.error_message:
                                st.error(f"Error: {result.error_message}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Packets Sent", result.packets_sent)
                            with col2:
                                st.metric("Packet Loss", f"{result.packet_loss_percent:.1f}%")
                        
                    except Exception as e:
                        st.error(f"Error running ping test: {str(e)}")
            else:
                st.warning("Please enter a target IP address or hostname")
    
    with test_tab2:
        st.subheader("🛤️ Traceroute Test")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            trace_target = st.text_input("Target (IP or hostname):", placeholder="google.com", key="trace_target")
        with col2:
            max_hops = st.number_input("Max Hops:", min_value=1, max_value=50, value=30)
        with col3:
            trace_timeout = st.number_input("Timeout (s):", min_value=1, max_value=30, value=5, key="trace_timeout")
        
        if st.button("🚀 Run Traceroute", type="primary"):
            if trace_target:
                with st.spinner(f"Tracing route to {trace_target}..."):
                    try:
                        result = asyncio.run(traceroute_host(trace_target, max_hops, trace_timeout))
                        
                        if result.success:
                            st.success(f"✅ Traceroute to {trace_target} completed!")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Hops", result.total_hops)
                            with col2:
                                st.metric("Target Reached", "✅ Yes" if result.target_reached else "❌ No")
                            with col3:
                                st.metric("Execution Time", f"{result.execution_time_ms:.0f}ms")
                            
                            # Hops table
                            st.subheader("🛤️ Route Path")
                            hops_data = []
                            for hop in result.hops:
                                if hop.timeout:
                                    hops_data.append({
                                        'Hop': hop.hop_number,
                                        'IP Address': '* * *',
                                        'Hostname': 'timeout',
                                        'Avg Latency (ms)': 'timeout'
                                    })
                                else:
                                    avg_latency = sum(hop.latency_ms) / len(hop.latency_ms) if hop.latency_ms else 0
                                    hops_data.append({
                                        'Hop': hop.hop_number,
                                        'IP Address': hop.ip_address or 'unknown',
                                        'Hostname': hop.hostname or 'unknown',
                                        'Avg Latency (ms)': f"{avg_latency:.2f}" if avg_latency > 0 else 'N/A'
                                    })
                            
                            if hops_data:
                                st.dataframe(pd.DataFrame(hops_data), use_container_width=True)
                        else:
                            st.error(f"❌ Traceroute to {trace_target} failed!")
                            if result.error_message:
                                st.error(f"Error: {result.error_message}")
                        
                    except Exception as e:
                        st.error(f"Error running traceroute: {str(e)}")
            else:
                st.warning("Please enter a target IP address or hostname")
    
    with test_tab3:
        st.subheader("📊 SNMP Device Monitor")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            snmp_target = st.text_input("Device IP:", placeholder="192.168.1.1", key="snmp_target")
        with col2:
            snmp_community = st.text_input("Community String:", value="public", key="snmp_community")
        
        if st.button("🚀 Query SNMP", type="primary"):
            if snmp_target:
                with st.spinner(f"Querying SNMP on {snmp_target}..."):
                    try:
                        result = asyncio.run(get_device_snmp_info(snmp_target, snmp_community))
                        
                        if result.success and result.device_info:
                            st.success(f"✅ SNMP query to {snmp_target} successful!")
                            
                            # Device information
                            st.subheader("🖥️ Device Information")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.info(f"**System Name:** {result.device_info.system_name}")
                                st.info(f"**System Description:** {result.device_info.system_description}")
                                st.info(f"**System Contact:** {result.device_info.system_contact}")
                                st.info(f"**System Location:** {result.device_info.system_location}")
                            
                            with col2:
                                uptime_days = result.device_info.system_uptime / 8640000 if result.device_info.system_uptime else 0
                                st.metric("Uptime", f"{uptime_days:.1f} days")
                                
                                if result.device_info.cpu_usage_percent is not None:
                                    st.metric("CPU Usage", f"{result.device_info.cpu_usage_percent:.1f}%")
                                
                                if result.device_info.memory_usage_percent is not None:
                                    st.metric("Memory Usage", f"{result.device_info.memory_usage_percent:.1f}%")
                            
                            # Interface information
                            if result.interfaces:
                                st.subheader("🔌 Interface Status")
                                interface_data = []
                                for iface in result.interfaces[:20]:  # Limit to 20 interfaces
                                    interface_data.append({
                                        'Interface': iface.interface_name,
                                        'Admin Status': '🟢 UP' if iface.admin_status == 'up' else '🔴 DOWN',
                                        'Oper Status': '🟢 UP' if iface.oper_status == 'up' else '🔴 DOWN',
                                        'Speed (Mbps)': f"{iface.speed_bps / 1000000:.0f}" if iface.speed_bps else 'N/A',
                                        'In Errors': iface.errors_in,
                                        'Out Errors': iface.errors_out
                                    })
                                
                                if interface_data:
                                    st.dataframe(pd.DataFrame(interface_data), use_container_width=True)
                        else:
                            st.error(f"❌ SNMP query to {snmp_target} failed!")
                            if result.error_message:
                                st.error(f"Error: {result.error_message}")
                        
                    except Exception as e:
                        st.error(f"Error running SNMP query: {str(e)}")
            else:
                st.warning("Please enter a device IP address")

elif page == "📊 Analytics":
    st.title("📊 Network Analytics")
    st.markdown("Historical data analysis and trends")
    
    # Time range selector
    col1, col2 = st.columns([1, 3])
    with col1:
        time_range = st.selectbox(
            "Time Range:",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom"]
        )
    
    # Get data based on time range
    session = db_manager.get_session()
    try:
        if time_range == "Last 24 Hours":
            start_time = datetime.now() - timedelta(days=1)
        elif time_range == "Last 7 Days":
            start_time = datetime.now() - timedelta(days=7)
        elif time_range == "Last 30 Days":
            start_time = datetime.now() - timedelta(days=30)
        else:
            with col2:
                start_date = st.date_input("Start Date:")
                start_time = datetime.combine(start_date, datetime.min.time())
        
        # Get test results in time range
        test_results = session.query(TestResult).filter(
            TestResult.timestamp >= start_time.timestamp()
        ).all()
        
    finally:
        session.close()
    
    if test_results:
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': datetime.fromtimestamp(test.timestamp),
                'test_type': test.test_type,
                'target': test.target,
                'status': test.status,
                'latency_ms': test.latency_ms or 0,
                'packet_loss': test.packet_loss or 0
            }
            for test in test_results
        ])
        
        # Success rate over time
        st.subheader("📈 Success Rate Trend")
        
        # Group by hour for success rate calculation
        df_hourly = df.set_index('timestamp').resample('H').agg({
            'status': lambda x: (x == 'success').mean() * 100,
            'test_type': 'count'
        }).rename(columns={'status': 'success_rate', 'test_type': 'test_count'})
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_hourly.index,
            y=df_hourly['success_rate'],
            mode='lines+markers',
            name='Success Rate (%)',
            line=dict(color='green', width=2)
        ))
        fig.update_layout(
            title="Network Success Rate Over Time",
            xaxis_title="Time",
            yaxis_title="Success Rate (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Latency analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⏱️ Latency Distribution")
            latency_data = df[df['latency_ms'] > 0]['latency_ms']
            
            if len(latency_data) > 0:
                fig = px.histogram(
                    latency_data,
                    nbins=30,
                    title="Latency Distribution",
                    labels={'value': 'Latency (ms)', 'count': 'Frequency'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No latency data available")
        
        with col2:
            st.subheader("🎯 Target Analysis")
            target_stats = df.groupby('target').agg({
                'status': lambda x: (x == 'success').mean() * 100,
                'latency_ms': 'mean',
                'test_type': 'count'
            }).rename(columns={
                'status': 'success_rate',
                'latency_ms': 'avg_latency',
                'test_type': 'test_count'
            }).round(2)
            
            target_stats = target_stats.sort_values('success_rate', ascending=False)
            st.dataframe(target_stats, use_container_width=True)
        
        # Performance summary
        st.subheader("📋 Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_tests = len(df)
            st.metric("Total Tests", total_tests)
        
        with col2:
            success_rate = (df['status'] == 'success').mean() * 100
            st.metric("Overall Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            avg_latency = df[df['latency_ms'] > 0]['latency_ms'].mean()
            st.metric("Average Latency", f"{avg_latency:.1f}ms" if not pd.isna(avg_latency) else "N/A")
        
        with col4:
            avg_packet_loss = df['packet_loss'].mean()
            st.metric("Average Packet Loss", f"{avg_packet_loss:.1f}%" if not pd.isna(avg_packet_loss) else "N/A")
    else:
        st.info("No data available for the selected time range")

elif page == "🚨 Alerts":
    st.title("🚨 Alert Management")
    st.markdown("Monitor and manage network alerts")
    
    # Alert status tabs
    alert_tab1, alert_tab2, alert_tab3 = st.tabs(["🔴 Active Alerts", "📋 All Alerts", "⚙️ Alert Settings"])
    
    session = db_manager.get_session()
    try:
        all_alerts = session.query(Alert).order_by(Alert.created_at.desc()).all()
        active_alerts = [alert for alert in all_alerts if alert.status == 'open']
    finally:
        session.close()
    
    with alert_tab1:
        st.subheader("🔴 Active Alerts")
        
        if active_alerts:
            for alert in active_alerts:
                severity_color = {
                    'low': '🟢',
                    'medium': '🟡', 
                    'high': '🟠',
                    'critical': '🔴'
                }.get(alert.severity, '⚪')
                
                with st.expander(f"{severity_color} {alert.title} - {alert.severity.upper()}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Description:** {alert.description}")
                        st.write(f"**Created:** {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        if alert.device_id:
                            st.write(f"**Device ID:** {alert.device_id}")
                    
                    with col2:
                        if alert.threshold_value and alert.current_value:
                            st.metric(
                                "Current vs Threshold",
                                f"{alert.current_value}",
                                f"Threshold: {alert.threshold_value}"
                            )
                        
                        # Action buttons
                        col_ack, col_resolve = st.columns(2)
                        with col_ack:
                            if st.button(f"✅ Acknowledge", key=f"ack_{alert.id}"):
                                st.success("Alert acknowledged!")
                        with col_resolve:
                            if st.button(f"🔧 Resolve", key=f"resolve_{alert.id}"):
                                st.success("Alert resolved!")
        else:
            st.success("🎉 No active alerts! Your network is running smoothly.")
    
    with alert_tab2:
        st.subheader("📋 All Alerts History")
        
        if all_alerts:
            # Create alerts DataFrame
            alerts_df = pd.DataFrame([
                {
                    'Time': alert.created_at.strftime('%Y-%m-%d %H:%M'),
                    'Severity': alert.severity.upper(),
                    'Title': alert.title,
                    'Status': alert.status.upper(),
                    'Device': f"Device {alert.device_id}" if alert.device_id else "N/A"
                }
                for alert in all_alerts[:50]  # Show last 50 alerts
            ])
            
            st.dataframe(alerts_df, use_container_width=True)
        else:
            st.info("No alerts in the system yet.")
    
    with alert_tab3:
        st.subheader("⚙️ Alert Configuration")
        
        st.markdown("**Threshold Settings:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            latency_threshold = st.number_input(
                "Latency Threshold (ms):",
                min_value=1,
                max_value=1000,
                value=100
            )
            
            packet_loss_threshold = st.number_input(
                "Packet Loss Threshold (%):",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.1
            )
        
        with col2:
            cpu_threshold = st.number_input(
                "CPU Usage Threshold (%):",
                min_value=1,
                max_value=100,
                value=90
            )
            
            memory_threshold = st.number_input(
                "Memory Usage Threshold (%):",
                min_value=1,
                max_value=100,
                value=85
            )
        
        if st.button("💾 Save Alert Settings"):
            st.success("Alert settings saved!")

elif page == "💬 Chat Interface":
    st.title("💬 AI Network Assistant")
    st.markdown("Chat with your network troubleshooting bot")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Describe your network issue or ask a question..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process with AI and display response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your request..."):
                try:
                    # Process query with AI intent handler
                    intent_result = process_user_query(
                        prompt,
                        openai_api_key=os.getenv("OPENAI_API_KEY")
                    )
                    
                    # Generate response based on intent
                    if intent_result.intent.value == "ping_test":
                        target = (intent_result.entities.get('ip_address') or 
                                intent_result.entities.get('hostname'))
                        
                        if target:
                            st.write(f"🔄 Running ping test to {target}...")
                            result = asyncio.run(ping_host(target))
                            
                            if result.success:
                                response = f"""✅ **Ping test successful!**
                                
Target: {target}
- Packet Loss: {result.packet_loss_percent:.1f}%
- Average Latency: {result.avg_latency_ms:.2f}ms
- Packets: {result.packets_received}/{result.packets_sent}

The target is reachable and responding normally."""
                            else:
                                response = f"""❌ **Ping test failed!**

Target: {target}
- Error: {result.error_message or 'Host unreachable'}
- Packet Loss: {result.packet_loss_percent:.1f}%

**Troubleshooting suggestions:**
1. Check if the target IP/hostname is correct
2. Verify your network connectivity
3. Check firewall settings
4. Try traceroute to identify where the connection fails"""
                        else:
                            response = """I understand you want to run a ping test, but I need to know the target.

Please specify:
- IP address (e.g., 8.8.8.8)
- Hostname (e.g., google.com)

Example: "ping 8.8.8.8" or "test connectivity to google.com" """
                    
                    elif intent_result.intent.value == "traceroute":
                        target = (intent_result.entities.get('ip_address') or 
                                intent_result.entities.get('hostname'))
                        
                        if target:
                            st.write(f"🔄 Running traceroute to {target}...")
                            result = asyncio.run(traceroute_host(target))
                            
                            if result.success:
                                response = f"""✅ **Traceroute completed!**

Target: {target}
- Total Hops: {result.total_hops}
- Target Reached: {'Yes' if result.target_reached else 'No'}
- Execution Time: {result.execution_time_ms:.0f}ms

Use the Live Testing tab to see detailed hop information."""
                            else:
                                response = f"""❌ **Traceroute failed!**

Target: {target}
- Error: {result.error_message or 'Unknown error'}

This could indicate network connectivity issues or routing problems."""
                        else:
                            response = """I understand you want to run traceroute, but I need a target.

Please specify:
- IP address (e.g., 1.1.1.1) 
- Hostname (e.g., google.com)

Example: "traceroute google.com" """
                    
                    elif intent_result.intent.value == "general_help":
                        response = """🤖 **Network Troubleshooting Assistant**

I can help you with:

🔍 **Connectivity Testing:**
- "ping 8.8.8.8"
- "test connectivity to server.com"
- "check if google.com is reachable"

🛤️ **Network Path Analysis:**
- "traceroute cloudflare.com"
- "show route to 1.1.1.1"

🔧 **Troubleshooting:**
- "interface eth0 is down"
- "high latency issues"
- "packet loss problems"

📊 **Device Monitoring:**
- "check device status"
- "SNMP query 192.168.1.1"

Just describe your network issue in natural language!"""
                    
                    else:
                        response = f"""I understand you want to: **{intent_result.suggested_action}**

Confidence: {intent_result.confidence:.0%}

However, I need more specific information to help you effectively.

**What I detected:**
- Intent: {intent_result.intent.value}
- Entities: {intent_result.entities if intent_result.entities else 'None'}

**Please provide more details or try:**
- Specific IP addresses or hostnames
- Clear description of the network issue
- Use commands like "ping X" or "traceroute Y" """
                    
                    st.write(response)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_response = f"Sorry, I encountered an error: {str(e)}\n\nPlease try rephrasing your question or use specific commands."
                    st.write(error_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_response})
    
    # Suggested prompts
    st.markdown("**💡 Try these examples:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏓 Ping Google DNS"):
            st.session_state.chat_history.append({"role": "user", "content": "ping 8.8.8.8"})
            st.rerun()
    
    with col2:
        if st.button("🛤️ Traceroute to Cloudflare"):
            st.session_state.chat_history.append({"role": "user", "content": "traceroute 1.1.1.1"})
            st.rerun()
    
    with col3:
        if st.button("❓ Help"):
            st.session_state.chat_history.append({"role": "user", "content": "help"})
            st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

elif page == "⚙️ Settings":
    st.title("⚙️ Settings & Configuration")
    st.markdown("Configure bot settings and preferences")
    
    # Configuration tabs
    config_tab1, config_tab2, config_tab3 = st.tabs(["🔧 General", "📧 Notifications", "🗄️ Database"])
    
    with config_tab1:
        st.subheader("🔧 General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dashboard Settings:**")
            refresh_interval = st.slider(
                "Auto-refresh interval (seconds):",
                min_value=10,
                max_value=300,
                value=30
            )
            
            max_history_days = st.number_input(
                "Max history to display (days):",
                min_value=1,
                max_value=90,
                value=7
            )
        
        with col2:
            st.markdown("**Testing Settings:**")
            default_ping_count = st.number_input(
                "Default ping count:",
                min_value=1,
                max_value=20,
                value=4
            )
            
            default_timeout = st.number_input(
                "Default timeout (seconds):",
                min_value=1,
                max_value=60,
                value=5
            )
        
        if st.button("💾 Save General Settings"):
            st.success("Settings saved!")
    
    with config_tab2:
        st.subheader("📧 Notification Settings")
        
        # Email settings
        st.markdown("**📧 Email Notifications:**")
        email_enabled = st.checkbox("Enable Email Notifications", value=True)
        
        if email_enabled:
            col1, col2 = st.columns(2)
            with col1:
                smtp_server = st.text_input("SMTP Server:", value="smtp.gmail.com")
                smtp_port = st.number_input("SMTP Port:", value=587)
            with col2:
                email_username = st.text_input("Email Username:")
                email_password = st.text_input("Email Password:", type="password")
        
        st.markdown("**📱 Slack Notifications:**")
        slack_enabled = st.checkbox("Enable Slack Notifications")
        
        if slack_enabled:
            slack_webhook = st.text_input("Slack Webhook URL:")
            slack_channel = st.text_input("Slack Channel:", value="#network-alerts")
        
        st.markdown("**📲 Telegram Notifications:**")
        telegram_enabled = st.checkbox("Enable Telegram Notifications")
        
        if telegram_enabled:
            telegram_token = st.text_input("Telegram Bot Token:", type="password")
            telegram_chat_id = st.text_input("Telegram Chat ID:")
        
        if st.button("💾 Save Notification Settings"):
            st.success("Notification settings saved!")
    
    with config_tab3:
        st.subheader("🗄️ Database Management")
        
        # Database statistics
        session = db_manager.get_session()
        try:
            device_count = session.query(Device).count()
            test_count = session.query(TestResult).count()
            alert_count = session.query(Alert).count()
        finally:
            session.close()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Devices", device_count)
        with col2:
            st.metric("Test Results", test_count)
        with col3:
            st.metric("Alerts", alert_count)
        
        st.markdown("**Database Actions:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 Clean Old Data"):
                st.info("This would clean data older than the configured retention period.")
        
        with col2:
            if st.button("📤 Export Data"):
                st.info("This would export database data to CSV files.")
        
        with col3:
            if st.button("🔄 Reset Database"):
                st.warning("This would reset all database tables. Use with caution!")

# Footer
st.markdown("---")
st.markdown("🌐 **Network Troubleshooting Bot Dashboard** | Real-time network monitoring and diagnostics")