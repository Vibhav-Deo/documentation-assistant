import streamlit as st
import requests
from config import API_URL

def render_organization_metrics():
    """Render organization-specific metrics"""
    st.subheader("🏢 Organization Overview")
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        
        with st.spinner("Loading organization data..."):
            response = requests.get(f"{API_URL}/monitoring/organization", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            org = data["organization"]
            users = data["users"]
            usage_stats = data["usage_stats"]
            
            # Organization info
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Organization", org["name"])
            
            with col2:
                st.metric("Plan", org["plan"].title())
            
            with col3:
                if org["plan"] == "enterprise":
                    st.metric("Quota", "Unlimited")
                else:
                    st.metric("Usage", f"{org['used_quota']}/{org['monthly_quota']}")
            
            with col4:
                st.metric("Total Users", len(users))
            
            # Users table
            st.subheader("👥 Organization Users")
            if users:
                user_data = []
                for user in users:
                    user_data.append({
                        "Name": user["name"],
                        "Email": user["email"],
                        "Role": user["role"].title(),
                        "Joined": user["created_at"][:10]
                    })
                st.dataframe(user_data, use_container_width=True)
            else:
                st.info("No users found")
            
            # Usage statistics
            st.subheader("📊 Usage Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total API Requests", usage_stats["total_requests"])
                
                # User request breakdown
                if usage_stats["user_requests"]:
                    st.write("**Requests by User:**")
                    for user_req in usage_stats["user_requests"][:5]:
                        st.write(f"• {user_req['name']}: {user_req['request_count']} requests")
            
            with col2:
                # Recent activity chart
                if usage_stats["recent_activity"]:
                    st.write("**Recent Activity (Last 30 Days):**")
                    activity_data = {}
                    for activity in usage_stats["recent_activity"]:
                        activity_data[str(activity["date"])] = activity["requests"]
                    
                    if activity_data:
                        st.bar_chart(activity_data)
                else:
                    st.info("No recent activity data")
        
        else:
            st.error(f"Failed to fetch organization data: {response.status_code}")
    
    except Exception as e:
        st.error(f"Error loading organization metrics: {e}")

def render_admin_panel():
    """Render admin panel for system monitoring"""
    if "user_info" not in st.session_state:
        return
    
    user = st.session_state.user_info["user"]
    if user["role"] != "admin":
        st.error("🚫 Admin access required")
        return
    
    st.title("🛠️ Admin Panel")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Organization", "System Health", "Request Metrics", "Alerts"])
    
    with tab1:
        render_organization_metrics()
    
    with tab2:
        render_system_health()
    
    with tab3:
        render_request_metrics()
    
    with tab4:
        render_alerts()

def render_system_health():
    """Render system health metrics"""
    st.subheader("System Health")
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        
        # Get health status
        health_response = requests.get(f"{API_URL}/health", headers=headers)
        if health_response.status_code == 200:
            health_data = health_response.json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status = health_data.get("status", "unknown")
                if status == "healthy":
                    st.success(f"✅ Status: {status.title()}")
                else:
                    st.error(f"❌ Status: {status.title()}")
            
            with col2:
                services = health_data.get("services", {})
                healthy_services = sum(1 for s in services.values() if s.get("status") == "healthy")
                total_services = len(services)
                st.info(f"🔧 Services: {healthy_services}/{total_services}")
            
            with col3:
                # Get system metrics
                metrics_response = requests.get(f"{API_URL}/metrics", headers=headers)
                if metrics_response.status_code == 200:
                    metrics = metrics_response.json()
                    cpu_percent = metrics.get("cpu_percent", 0)
                    if cpu_percent > 80:
                        st.error(f"🔥 CPU: {cpu_percent}%")
                    else:
                        st.success(f"💻 CPU: {cpu_percent}%")
            
            # Service details
            st.subheader("Service Status")
            for service, details in services.items():
                status = details.get("status", "unknown")
                if status == "healthy":
                    st.success(f"✅ {service.title()}: {status}")
                else:
                    st.error(f"❌ {service.title()}: {status}")
                    if "error" in details:
                        st.error(f"   Error: {details['error']}")
        
        else:
            st.error("Failed to fetch health data")
    
    except Exception as e:
        st.error(f"Error: {e}")

def render_request_metrics():
    """Render request metrics"""
    st.subheader("Request Metrics")
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        
        # Time period selector
        hours = st.selectbox("Time Period", [1, 6, 24, 168], index=2, format_func=lambda x: f"Last {x} hours" if x < 24 else f"Last {x//24} days")
        
        response = requests.get(f"{API_URL}/monitoring/requests?hours={hours}", headers=headers)
        if response.status_code == 200:
            metrics = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Requests", metrics.get("total_requests", 0))
            
            with col2:
                avg_time = metrics.get("avg_response_time", 0)
                st.metric("Avg Response Time", f"{avg_time}s")
            
            with col3:
                error_rate = metrics.get("error_rate", 0)
                st.metric("Error Rate", f"{error_rate}%")
            
            with col4:
                st.metric("Period", f"{hours}h")
            
            # Status codes
            status_codes = metrics.get("status_codes", {})
            if status_codes:
                st.subheader("Status Code Distribution")
                for code, count in status_codes.items():
                    st.write(f"**{code}**: {count} requests")
            
            # Top endpoints
            endpoints = metrics.get("top_endpoints", {})
            if endpoints:
                st.subheader("Top Endpoints")
                for endpoint, count in list(endpoints.items())[:10]:
                    st.write(f"**{endpoint}**: {count} requests")
        
        else:
            st.error("Failed to fetch metrics data")
    
    except Exception as e:
        st.error(f"Error: {e}")

def render_alerts():
    """Render system alerts"""
    st.subheader("System Alerts")
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        
        response = requests.get(f"{API_URL}/monitoring/alerts", headers=headers)
        if response.status_code == 200:
            alerts = response.json()
            
            if not alerts:
                st.success("✅ No active alerts")
            else:
                for alert in alerts:
                    alert_type = alert.get("type", "info")
                    message = alert.get("message", "")
                    timestamp = alert.get("timestamp", "")
                    
                    if alert_type == "critical":
                        st.error(f"🚨 **CRITICAL**: {message}")
                    elif alert_type == "warning":
                        st.warning(f"⚠️ **WARNING**: {message}")
                    else:
                        st.info(f"ℹ️ **INFO**: {message}")
                    
                    st.caption(f"Time: {timestamp}")
        
        else:
            st.error("Failed to fetch alerts")
    
    except Exception as e:
        st.error(f"Error: {e}")