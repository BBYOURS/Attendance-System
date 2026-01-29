# attendance_system.py
import streamlit as st
import requests
import datetime
import time
import json
import os

# Session state keys
SESSION_KEYS = [
    'session_token', 'employee_id', 'employee_name', 
    'role', 'last_activity'
]

# Initialize session state
for key in SESSION_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None

# ==============================================
# 1. UTILITY FUNCTIONS
# ==============================================

def call_gas_endpoint(action, data=None):
    """Call Google Apps Script endpoint"""
    try:
        # Try to get GAS endpoint from multiple sources
        GAS_ENDPOINT = ""
        
        # First try: Streamlit secrets
        try:
            GAS_ENDPOINT = st.secrets.get("GAS_ENDPOINT", "")
        except:
            pass
        
        # Second try: Environment variable
        if not GAS_ENDPOINT:
            GAS_ENDPOINT = os.environ.get("GAS_ENDPOINT", "")
        
        # Third try: Hardcoded (TEMPORARY ONLY)
        if not GAS_ENDPOINT or "YOUR_GAS" in GAS_ENDPOINT:
            st.error("⚠️ GAS_ENDPOINT not configured")
            st.info("Please add to .streamlit/secrets.toml:\nGAS_ENDPOINT = \"YOUR_GAS_URL\"")
            return {"success": False, "message": "System not configured"}
        
        payload = {'action': action}
        if data:
            payload.update(data)
        
        if action != 'login' and st.session_state.session_token:
            payload['sessionToken'] = st.session_state.session_token
        
        # Make request with timeout
        response = requests.post(
            GAS_ENDPOINT, 
            json=payload, 
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if response is valid JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            return {
                "success": False, 
                "message": f"Invalid response from server. Status: {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Connection timeout (30s). Server might be busy."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot connect to server. Check URL."}
    except Exception as e:
        return {"success": False, "message": f"System error: {str(e)}"}

def check_session():
    """Check if session is valid"""
    if not st.session_state.session_token:
        return False
    
    # Check idle timeout (10 minutes)
    if st.session_state.last_activity:
        idle_time = datetime.datetime.now() - st.session_state.last_activity
        if idle_time.total_seconds() > 600:
            logout()
            return False
    
    # Update last activity
    st.session_state.last_activity = datetime.datetime.now()
    return True

def logout():
    """Clear session and logout"""
    for key in SESSION_KEYS:
        st.session_state[key] = None
    st.rerun()

# ==============================================
# 2. SIMPLIFIED LOGIN PAGE
# ==============================================

def login_page():
    """Simple login page"""
    st.title("🏢 Attendance & Inventory System")
    st.markdown("---")
    
    # Configuration check
    try:
        gas_url = st.secrets.get("GAS_ENDPOINT", "")
        if not gas_url or "YOUR_GAS" in gas_url:
            with st.expander("⚠️ Configuration Required", expanded=True):
                st.error("GAS_ENDPOINT not configured!")
                st.markdown("""
                **Steps to fix:**
                1. Create `.streamlit/secrets.toml` file
                2. Add: `GAS_ENDPOINT = "YOUR_GAS_URL"`
                3. Get GAS_URL from Google Apps Script deployment
                """)
                return
    except:
        pass
    
    with st.form("login_form"):
        st.subheader("Login")
        
        employee_id = st.text_input("Employee ID", placeholder="Enter your Employee ID")
        password = st.text_input("Password", type="password", placeholder="Enter 12-character password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("🔐 Login", use_container_width=True)
        with col2:
            clear_btn = st.form_submit_button("🗑️ Clear", use_container_width=True)
        
        if clear_btn:
            st.rerun()
        
        if login_btn:
            if not employee_id or not password:
                st.error("Please enter both Employee ID and Password")
            elif len(password) != 12:
                st.error("Password must be exactly 12 characters")
            else:
                with st.spinner("Authenticating..."):
                    # SIMULATED LOGIN FOR TESTING
                    # Remove this in production
                    if employee_id == "admin" and password == "admin123456":
                        st.session_state.session_token = "demo_token"
                        st.session_state.employee_id = "admin"
                        st.session_state.employee_name = "Admin User"
                        st.session_state.role = "ADMIN"
                        st.session_state.last_activity = datetime.datetime.now()
                        st.success("Login successful (Demo Mode)")
                        time.sleep(1)
                        st.rerun()
                    else:
                        # Actual GAS call
                        result = call_gas_endpoint('login', {
                            'employeeId': employee_id.strip(),
                            'password': password.strip()
                        })
                        
                        if result and result.get('success'):
                            st.session_state.session_token = result['sessionToken']
                            st.session_state.employee_id = employee_id.strip()
                            st.session_state.employee_name = result['employeeName']
                            st.session_state.role = result['role']
                            st.session_state.last_activity = datetime.datetime.now()
                            
                            st.success(f"Welcome {result['employeeName']}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            error_msg = result.get('message', 'Login failed') if result else 'Connection error'
                            st.error(f"Login failed: {error_msg}")

# ==============================================
# 3. SIMPLIFIED DASHBOARD
# ==============================================

def employee_dashboard():
    """Simple employee dashboard"""
    if not check_session():
        st.warning("Session expired. Please login again.")
        logout()
        return
    
    st.title(f"👋 Welcome, {st.session_state.employee_name}")
    st.markdown(f"**Employee ID:** {st.session_state.employee_id} | **Role:** {st.session_state.role}")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["⏰ Attendance", "📦 Inventory", "💰 Payslip"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 Clock In", use_container_width=True):
                st.info("Clock In feature coming soon")
        with col2:
            if st.button("🔴 Clock Out", use_container_width=True):
                st.info("Clock Out feature coming soon")
        
        st.markdown("---")
        st.subheader("Today's Status")
        st.info("Not clocked in yet")
    
    with tab2:
        st.subheader("Inventory Access")
        st.warning("You must be clocked in to access inventory")
        
        st.markdown("---")
        st.subheader("Available Items")
        st.info("Inventory list will appear here when clocked in")
    
    with tab3:
        st.subheader("Payslip")
        st.info("Payslip data available at end of pay period")
        
        # Demo payslip
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Gross Pay", "₱25,000.00")
            st.metric("Deductions", "₱2,500.00")
        with col2:
            st.metric("Allowances", "₱1,000.00")
            st.metric("Net Pay", "₱23,500.00")
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

def admin_dashboard():
    """Admin dashboard"""
    if not check_session() or st.session_state.role != "ADMIN":
        st.error("Unauthorized access")
        logout()
        return
    
    st.title("👑 Admin Dashboard")
    st.markdown("---")
    
    # Admin tabs
    tab1, tab2 = st.tabs(["👥 Employee Management", "📊 System Logs"])
    
    with tab1:
        st.subheader("Employee List")
        st.info("Manage employees directly in Google Sheets")
        
        # Sample employee table
        employees = [
            {"ID": "EMP001", "Name": "Juan Dela Cruz", "Position": "Manager", "Status": "Active"},
            {"ID": "EMP002", "Name": "Maria Santos", "Position": "Staff", "Status": "Active"},
            {"ID": "EMP003", "Name": "Pedro Reyes", "Position": "Staff", "Status": "Inactive"},
        ]
        st.dataframe(employees, use_container_width=True)
    
    with tab2:
        st.subheader("Security Logs")
        st.info("Logs are recorded in Google Sheets Security Log tab")
        
        # Sample logs
        logs = [
            {"Timestamp": "2024-01-20 09:00", "Action": "LOGIN", "User": "EMP001", "Status": "SUCCESS"},
            {"Timestamp": "2024-01-20 09:05", "Action": "CLOCK_IN", "User": "EMP001", "Status": "SUCCESS"},
            {"Timestamp": "2024-01-20 17:00", "Action": "CLOCK_OUT", "User": "EMP001", "Status": "SUCCESS"},
        ]
        st.dataframe(logs, use_container_width=True)
    
    # Logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

# ==============================================
# 4. MAIN APP
# ==============================================

def main():
    # Page configuration
    st.set_page_config(
        page_title="Attendance System",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Hide Streamlit branding
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Simple routing
    if not st.session_state.session_token:
        login_page()
    elif st.session_state.role == "ADMIN":
        admin_dashboard()
    else:
        employee_dashboard()

if __name__ == "__main__":
    main()