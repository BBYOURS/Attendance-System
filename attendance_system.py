# attendance_system.py
# ==============================================
# STREAMLIT FRONTEND - UI ONLY
# MASTER POLICY COMPLIANT - NO DIRECT SHEET ACCESS
# ==============================================

import streamlit as st
import requests
import datetime
import time

# Session state keys
SESSION_KEYS = [
    'session_token', 'employee_id', 'employee_name', 
    'role', 'last_activity', 'clocked_in_today'
]

# Initialize session state
for key in SESSION_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None

# ==============================================
# 1. UTILITY FUNCTIONS (FIXED)
# ==============================================

def call_gas_endpoint(action, data=None):
    """Call Google Apps Script endpoint"""
    try:
        # Get GAS endpoint from secrets
        GAS_ENDPOINT = st.secrets.get("GAS_ENDPOINT", "")
        
        if not GAS_ENDPOINT or GAS_ENDPOINT == "YOUR_GAS_WEB_APP_URL":
            return {"success": False, "message": "System not configured. Please contact admin."}
        
        payload = {'action': action}
        if data:
            payload.update(data)
        
        if action != 'login' and st.session_state.session_token:
            payload['sessionToken'] = st.session_state.session_token
        
        response = requests.post(GAS_ENDPOINT, json=payload, timeout=10)
        return response.json()
        
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Connection timeout. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot connect to server. Check your internet."}
    except Exception as e:
        return {"success": False, "message": f"System error: {str(e)}"}

def check_session():
    """Check if session is valid"""
    if not st.session_state.session_token:
        return False
    
    # Check idle timeout
    if st.session_state.last_activity:
        idle_time = datetime.datetime.now() - st.session_state.last_activity
        if idle_time.total_seconds() > 600:  # 10 minutes idle timeout
            logout()
            return False
    
    # Update last activity
    st.session_state.last_activity = datetime.datetime.now()
    
    # Verify with backend
    result = call_gas_endpoint('checkSession')
    return result and result.get('valid', False)

def logout():
    """Clear session and logout"""
    if st.session_state.session_token:
        call_gas_endpoint('logout')
    
    for key in SESSION_KEYS:
        st.session_state[key] = None
    
    st.rerun()

def require_auth():
    """Require authentication for page access"""
    if not check_session():
        st.warning("Please login to access this page")
        st.stop()

def require_role(required_role):
    """Require specific role for page access"""
    require_auth()
    if st.session_state.role != required_role:
        st.error("Unauthorized access")
        st.stop()

# ==============================================
# 2. PAGE COMPONENTS (UPDATED WITH PASSWORD)
# ==============================================

def login_page():
    """Login page"""
    st.title("🔐 Attendance & Inventory System")
    st.markdown("---")
    
    with st.form("login_form"):
        employee_id = st.text_input("Employee ID")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Login")
        with col2:
            if st.form_submit_button("Clear"):
                st.rerun()
        
        if submitted:
            if not employee_id or not password:
                st.error("Please enter both Employee ID and Password")
            else:
                with st.spinner("Logging in..."):
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

def employee_dashboard():
    """Employee dashboard"""
    require_auth()
    
    st.title(f"👋 Welcome, {st.session_state.employee_name}")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["⏰ Attendance", "📦 Inventory", "💰 Payslip"])
    
    with tab1:
        attendance_tab()
    
    with tab2:
        inventory_tab()
    
    with tab3:
        payslip_tab()
    
    # Logout button in sidebar
    with st.sidebar:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"ID: {st.session_state.employee_id}")
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                logout()

def attendance_tab():
    """Attendance management tab"""
    st.header("Attendance Management")
    
    # Get today's attendance status
    result = call_gas_endpoint('getTodayAttendance')
    
    clocked_in = False
    clock_out_time = None
    
    if result and result.get('success'):
        clocked_in = result.get('clockedIn', False)
        clock_out_time = result.get('clockOutTime')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Clock In")
        if not clocked_in:
            if st.button("🟢 Clock In Now", use_container_width=True, type="primary"):
                result = call_gas_endpoint('clockIn')
                if result and result.get('success'):
                    st.success("✓ Clocked in successfully!")
                    time.sleep(1)
                    st.rerun()
                elif result and result.get('requiresOTP'):
                    st.session_state.otp_purpose = 'EARLYCLOCKIN'
                    st.session_state.otp_action = 'clockIn'
                    st.rerun()
                else:
                    error_msg = result.get('message', 'Clock in failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
        else:
            st.success("✅ Already clocked in today")
    
    with col2:
        st.subheader("Clock Out")
        if clocked_in and not clock_out_time:
            if st.button("🔴 Clock Out Now", use_container_width=True, type="secondary"):
                result = call_gas_endpoint('clockOut')
                if result and result.get('success'):
                    st.success("✓ Clocked out successfully!")
                    time.sleep(1)
                    st.rerun()
                elif result and result.get('requiresOTP'):
                    st.session_state.otp_purpose = 'OVERTIME'
                    st.session_state.otp_action = 'clockOut'
                    st.rerun()
                else:
                    error_msg = result.get('message', 'Clock out failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
        elif clock_out_time:
            st.info(f"✅ Clocked out at {clock_out_time}")
        else:
            st.info("⏰ Ready to clock out")
    
    with col3:
        st.subheader("Status")
        if clocked_in:
            st.metric("Status", "CLOCKED IN", "Active")
        else:
            st.metric("Status", "NOT CLOCKED IN", "Inactive")
        
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
    
    # OTP Flow
    if 'otp_purpose' in st.session_state and st.session_state.otp_purpose:
        handle_otp_flow(st.session_state.otp_purpose, st.session_state.otp_action)

def inventory_tab():
    """Inventory management tab"""
    st.header("Inventory Management")
    
    # Check if clocked in
    result = call_gas_endpoint('getTodayAttendance')
    if not result or not result.get('success') or not result.get('clockedIn'):
        st.warning("⚠️ You must be clocked in to access inventory")
        return
    
    # Get available inventory
    result = call_gas_endpoint('getInventory')
    
    if result and result.get('success'):
        items = result.get('items', [])
        
        if not items:
            st.info("📭 No inventory items available")
            return
        
        with st.form("inventory_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                item_options = {item['product']: item for item in items}
                selected_item = st.selectbox(
                    "Select Item",
                    options=list(item_options.keys())
                )
            
            with col2:
                quantity = st.number_input("Quantity", 
                                         min_value=1, 
                                         max_value=50, 
                                         value=1,
                                         help="Maximum 50 items per day")
            
            with col3:
                if selected_item in item_options:
                    unit_price = item_options[selected_item]['sellingPrice']
                    total_price = quantity * unit_price
                    st.metric("Unit Price", f"₱{unit_price:,.2f}")
                    st.metric("Total", f"₱{total_price:,.2f}")
            
            submitted = st.form_submit_button("📦 Use Item", type="primary", use_container_width=True)
            
            if submitted and selected_item in item_options:
                with st.spinner("Processing transaction..."):
                    result = call_gas_endpoint('useInventory', {
                        'item': selected_item,
                        'quantity': quantity,
                        'unitPrice': unit_price
                    })
                
                if result and result.get('success'):
                    st.success(f"✅ Transaction completed!")
                    st.code(f"Transaction ID: {result.get('transactionId')}")
                    time.sleep(2)
                    st.rerun()
                else:
                    error_msg = result.get('message', 'Transaction failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
    else:
        st.error("❌ Unable to load inventory")

def payslip_tab():
    """Payslip viewing tab"""
    st.header("💰 Payslip Viewer")
    
    # Month selector
    current_month = datetime.datetime.now().strftime("%B %Y")
    month = st.selectbox(
        "Select Month",
        options=[current_month],
        disabled=True
    )
    
    # Get payslip data
    result = call_gas_endpoint('getPayslip')
    
    if result and result.get('success'):
        payslip = result.get('payslip', {})
        
        # Display payslip in a nice card
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Employee Info")
            st.info(f"**Name:** {payslip.get('name', 'N/A')}")
            st.info(f"**Gender:** {payslip.get('gender', 'N/A')}")
            st.info(f"**Position:** {payslip.get('position', 'N/A')}")
        
        with col2:
            st.markdown("### Earnings & Deductions")
            st.success(f"**Gross Pay:** ₱{payslip.get('gross', 0):,.2f}")
            st.warning(f"**Deductions:** ₱{payslip.get('deductions', 0):,.2f}")
        
        st.markdown("---")
        st.markdown(f"### 📄 Net Pay: ₱{payslip.get('netPay', 0):,.2f}")
        
        # Security note
        with st.expander("ℹ️ Security Notice"):
            st.warning("""
            **Security Policy:**
            - Payslip is read-only
            - No export/download available
            - Data is protected and encrypted
            - Viewing is logged for security audit
            """)
    else:
        st.info("📅 Payslip data will be available at the end of the pay period")

def handle_otp_flow(purpose, action):
    """Handle OTP requirement flow"""
    st.warning(f"🔐 {purpose.replace('_', ' ').title()} requires OTP verification")
    
    with st.form("otp_form"):
        otp = st.text_input("Enter 6-digit OTP", 
                          max_chars=6,
                          placeholder="123456",
                          help="Check your registered email for OTP")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_otp = st.form_submit_button("✅ Verify OTP", use_container_width=True)
        with col2:
            request_otp = st.form_submit_button("📧 Send OTP", use_container_width=True)
        with col3:
            cancel_otp = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if cancel_otp:
            if 'otp_purpose' in st.session_state:
                del st.session_state.otp_purpose
            if 'otp_action' in st.session_state:
                del st.session_state.otp_action
            st.rerun()
        
        if request_otp:
            with st.spinner("Sending OTP..."):
                result = call_gas_endpoint('generateOTP', {'purpose': purpose})
            if result and result.get('success'):
                st.success("✓ OTP sent to your registered email")
            else:
                error_msg = result.get('message', 'Failed to send OTP') if result else 'Error'
                st.error(f"✗ {error_msg}")
        
        if submit_otp:
            if len(otp) != 6 or not otp.isdigit():
                st.error("Invalid OTP format. Must be 6 digits.")
            else:
                with st.spinner("Verifying OTP..."):
                    result = call_gas_endpoint(action, {'otp': otp})
                if result and result.get('success'):
                    st.success("✓ OTP verified successfully!")
                    time.sleep(1)
                    if 'otp_purpose' in st.session_state:
                        del st.session_state.otp_purpose
                    if 'otp_action' in st.session_state:
                        del st.session_state.otp_action
                    st.rerun()
                else:
                    error_msg = result.get('message', 'Invalid OTP') if result else 'Error'
                    st.error(f"✗ {error_msg}")

def admin_dashboard():
    """Admin dashboard"""
    require_role('ADMIN')
    
    st.title("👑 Admin Dashboard")
    st.markdown("---")
    
    # Admin tabs
    tab1, tab2, tab3 = st.tabs(["📋 Approvals", "👥 Employees", "📊 Logs"])
    
    with tab1:
        st.header("Pending Approvals")
        st.info("Check your email for approval requests and click the approval links.")
        
        # Manual approval entry
        with st.expander("📝 Manual Approval Entry"):
            col1, col2 = st.columns(2)
            with col1:
                emp_id = st.text_input("Employee ID")
                approval_type = st.selectbox("Type", ["EARLYCLOCKIN", "OVERTIME", "SHIFTCHANGE"])
            with col2:
                approval_date = st.date_input("Date", datetime.datetime.now())
                action = st.selectbox("Action", ["APPROVE", "REJECT"])
            
            if st.button("Process Approval", type="primary"):
                result = call_gas_endpoint('adminApprove', {
                    'employeeId': emp_id,
                    'type': approval_type,
                    'date': str(approval_date),
                    'approved': action == "APPROVE"
                })
                if result and result.get('success'):
                    st.success("✓ Approval processed")
                else:
                    error_msg = result.get('message', 'Failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
    
    with tab2:
        st.header("Employee Management")
        
        # View all employees
        if st.button("🔄 Load Employees", type="secondary"):
            result = call_gas_endpoint('getAllEmployees')
            if result and result.get('success'):
                employees = result.get('employees', [])
                if employees:
                    st.dataframe(employees, use_container_width=True)
                else:
                    st.info("No employee data found")
            else:
                st.error("Failed to load employees")
        
        st.info("For detailed employee management, please use Google Sheets directly.")
    
    with tab3:
        st.header("Security Logs")
        
        # View recent logs
        col1, col2 = st.columns(2)
        with col1:
            log_limit = st.number_input("Log entries", min_value=10, max_value=100, value=20)
        with col2:
            log_severity = st.selectbox("Severity", ["ALL", "INFO", "WARNING", "ERROR", "HIGH"])
        
        if st.button("📋 View Logs", type="primary"):
            result = call_gas_endpoint('getRecentLogs', {'limit': log_limit})
            if result and result.get('success'):
                logs = result.get('logs', [])
                if logs:
                    st.dataframe(logs, use_container_width=True)
                else:
                    st.info("No logs found")
            else:
                st.error("Failed to load logs")
    
    with st.sidebar:
        st.markdown("---")
        st.info(f"Admin: {st.session_state.employee_name}")
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()

# ==============================================
# 3. MAIN APPLICATION
# ==============================================

def main():
    # Configure page
    st.set_page_config(
        page_title="Attendance & Inventory System",
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
        .stDeployButton {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Check for GAS endpoint configuration
    if 'GAS_ENDPOINT' not in st.secrets or st.secrets['GAS_ENDPOINT'] == "YOUR_GAS_WEB_APP_URL":
        st.error("⚠️ System Not Configured")
        st.markdown("""
        **Please follow these steps:**
        
        1. **Deploy Google Apps Script:**
           - Go to [script.google.com](https://script.google.com)
           - Create new project
           - Copy GAS code
           - Deploy as Web App
           - Copy the Web App URL
        
        2. **Configure secrets.toml:**
           ```toml
           # .streamlit/secrets.toml
           GAS_ENDPOINT = "YOUR_COPIED_URL_HERE"
           ```
        
        3. **Restart the app**
        """)
        return
    
    # Session timeout check
    if st.session_state.session_token:
        if not check_session():
            st.warning("Session expired. Please login again.")
            logout()
    
    # Route to appropriate page
    if not st.session_state.session_token:
        login_page()
    elif st.session_state.role == 'ADMIN':
        admin_dashboard()
    else:
        employee_dashboard()

if __name__ == "__main__":
    main()