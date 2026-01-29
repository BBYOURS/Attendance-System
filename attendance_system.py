# attendance_system.py
# ==============================================
# STREAMLIT FRONTEND - UI ONLY
# MASTER POLICY COMPLIANT - NO DIRECT SHEET ACCESS
# ==============================================

import streamlit as st
import requests
import datetime
import time

# GAS endpoint from secrets.toml
GAS_ENDPOINT = st.secrets["GAS_ENDPOINT"]

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
# 1. UTILITY FUNCTIONS
# ==============================================

def call_gas_endpoint(action, data=None):
    """Call Google Apps Script endpoint"""
    try:
        payload = {'action': action}
        if data:
            payload.update(data)
        
        if action != 'login' and st.session_state.session_token:
            payload['sessionToken'] = st.session_state.session_token
        
        response = requests.post(GAS_ENDPOINT, json=payload)
        return response.json()
    except Exception as e:
        st.error("Connection error. Please try again.")
        return None

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
# 2. PAGE COMPONENTS
# ==============================================

def login_page():
    """Login page"""
    st.title("🔐 Attendance & Inventory System")
    st.markdown("---")
    
    with st.form("login_form"):
        name = st.text_input("Full Name")
        employee_id = st.text_input("Employee ID", type="password")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Login")
        with col2:
            if st.form_submit_button("Clear"):
                st.rerun()
        
        if submitted:
            if not name or not employee_id:
                st.error("Please enter both name and employee ID")
            else:
                result = call_gas_endpoint('login', {
                    'name': name.strip(),
                    'employeeId': employee_id.strip()
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
                    st.error(result.get('message', 'Login failed'))

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
        if st.button("🚪 Logout", use_container_width=True):
            logout()

def attendance_tab():
    """Attendance management tab"""
    st.header("Attendance Management")
    
    # Check if already clocked in today
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    result = call_gas_endpoint('getTodayAttendance', {'date': today})
    
    clocked_in_today = False
    clock_out_time = None
    
    if result and result.get('success'):
        attendance = result.get('attendance', {})
        clocked_in_today = attendance.get('clockedIn', False)
        clock_out_time = attendance.get('clockOutTime')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not clocked_in_today:
            if st.button("🟢 Clock In", use_container_width=True, type="primary"):
                result = call_gas_endpoint('clockIn', {'notes': 'ONTIMECLOCKIN'})
                
                if result and result.get('success'):
                    st.success("Clocked in successfully!")
                    st.rerun()
                elif result and result.get('requiresOTP'):
                    handle_otp_flow('EARLYCLOCKIN', 'clockIn')
                else:
                    st.error(result.get('message', 'Clock in failed'))
        else:
            st.info("✅ Clocked in today")
    
    with col2:
        if clocked_in_today and not clock_out_time:
            if st.button("🔴 Clock Out", use_container_width=True, type="secondary"):
                result = call_gas_endpoint('clockOut', {'notes': 'ONTIMECLOCKOUT'})
                
                if result and result.get('success'):
                    st.success("Clocked out successfully!")
                    st.rerun()
                elif result and result.get('requiresOTP'):
                    handle_otp_flow('OVERTIME', 'clockOut')
                else:
                    st.error(result.get('message', 'Clock out failed'))
        elif clock_out_time:
            st.info(f"✅ Clocked out at {clock_out_time}")
        else:
            st.info("🕐 Ready to clock out")
    
    with col3:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()

def inventory_tab():
    """Inventory management tab"""
    st.header("Inventory Management")
    
    # Check if clocked in
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    result = call_gas_endpoint('getTodayAttendance', {'date': today})
    
    if not result or not result.get('success') or not result.get('attendance', {}).get('clockedIn'):
        st.warning("You must be clocked in to access inventory")
        return
    
    # Get available inventory
    result = call_gas_endpoint('getInventory')
    
    if result and result.get('success'):
        items = result.get('items', [])
        
        with st.form("inventory_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                item_options = {item['product']: item for item in items}
                selected_item = st.selectbox(
                    "Item",
                    options=list(item_options.keys()) if item_options else ["No items available"]
                )
            
            with col2:
                quantity = st.number_input("Quantity", min_value=1, max_value=50, value=1)
            
            with col3:
                if selected_item != "No items available" and selected_item in item_options:
                    unit_price = item_options[selected_item]['sellingPrice']
                    st.metric("Unit Price", f"₱{unit_price:,.2f}")
                    total_price = quantity * unit_price
                    st.metric("Total", f"₱{total_price:,.2f}")
                else:
                    st.metric("Unit Price", "₱0.00")
                    st.metric("Total", "₱0.00")
            
            submitted = st.form_submit_button("Use Item", type="primary", disabled=selected_item=="No items available")
            
            if submitted and selected_item != "No items available":
                result = call_gas_endpoint('useInventory', {
                    'item': selected_item,
                    'quantity': quantity,
                    'unitPrice': unit_price
                })
                
                if result and result.get('success'):
                    st.success(f"✅ Transaction ID: {result.get('transactionId')}")
                else:
                    st.error(result.get('message', 'Transaction failed'))
    else:
        st.error("Unable to load inventory")

def payslip_tab():
    """Payslip viewing tab"""
    st.header("Payslip Viewer")
    
    # Month selector
    current_month = datetime.datetime.now().strftime("%Y-%m")
    month = st.selectbox(
        "Select Month",
        options=[current_month],
        disabled=True
    )
    
    # Get payslip data
    result = call_gas_endpoint('getPayslip', {'month': month})
    
    if result and result.get('success'):
        payslip = result.get('payslip', {})
        
        # Display payslip
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Employee Name", payslip.get('name', 'N/A'))
            st.metric("Gender", payslip.get('gender', 'N/A'))
        
        with col2:
            st.metric("Gross Pay", f"₱{payslip.get('gross', 0):,.2f}")
            st.metric("Deductions", f"₱{payslip.get('deductions', 0):,.2f}")
        
        st.markdown("---")
        st.metric("**Net Pay**", f"₱{payslip.get('netPay', 0):,.2f}", delta_color="off")
        
        st.info("Payslip is read-only. No export available per security policy.")
    else:
        st.info("Payslip data will be available at the end of the pay period")

def handle_otp_flow(purpose, action):
    """Handle OTP requirement flow"""
    st.warning(f"{purpose.replace('_', ' ').title()} requires OTP verification")
    
    with st.form("otp_form"):
        otp = st.text_input("Enter 6-digit OTP", max_chars=6)
        
        col1, col2 = st.columns(2)
        with col1:
            submit_otp = st.form_submit_button("Verify OTP")
        with col2:
            request_otp = st.form_submit_button("Send New OTP")
        
        if request_otp:
            result = call_gas_endpoint('generateOTP', {'purpose': purpose})
            if result and result.get('success'):
                st.success("OTP sent to your registered email")
            else:
                st.error("Failed to send OTP")
        
        if submit_otp:
            if len(otp) != 6 or not otp.isdigit():
                st.error("Invalid OTP format")
            else:
                # Retry the original action with OTP
                result = call_gas_endpoint(action, {'otp': otp})
                if result and result.get('success'):
                    st.success("Verified successfully!")
                    st.rerun()
                else:
                    st.error("Invalid OTP")

def admin_dashboard():
    """Admin dashboard"""
    require_role('ADMIN')
    
    st.title("👑 Admin Dashboard")
    st.markdown("---")
    
    # Admin tabs
    tab1, tab2, tab3 = st.tabs(["📋 Approvals", "👥 Employee Management", "📊 Logs"])
    
    with tab1:
        st.header("Pending Approvals")
        st.info("Approval system accessed via email links per security policy")
        
        # Display pending approvals
        result = call_gas_endpoint('getPendingApprovals')
        if result and result.get('success'):
            approvals = result.get('approvals', [])
            if approvals:
                for approval in approvals:
                    with st.expander(f"{approval['type']} - {approval['employeeName']}"):
                        st.write(f"Date: {approval['date']}")
                        st.write(f"Details: {approval['details']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Approve {approval['id']}", key=f"approve_{approval['id']}"):
                                call_gas_endpoint('adminApprove', {
                                    'approvalId': approval['id'],
                                    'approved': True
                                })
                                st.success("Approved!")
                                st.rerun()
                        with col2:
                            if st.button(f"Deny {approval['id']}", key=f"deny_{approval['id']}"):
                                call_gas_endpoint('adminApprove', {
                                    'approvalId': approval['id'],
                                    'approved': False
                                })
                                st.warning("Denied!")
                                st.rerun()
            else:
                st.success("No pending approvals")
    
    with tab2:
        st.header("Employee Management")
        st.info("Employee profiles managed directly in Google Sheets per security policy")
        
        # View employee list
        result = call_gas_endpoint('getAllEmployees')
        if result and result.get('success'):
            employees = result.get('employees', [])
            st.dataframe(employees, use_container_width=True)
    
    with tab3:
        st.header("Security Logs")
        st.info("Security logs available in Google Sheets Security Log tab")
        
        # View recent logs
        result = call_gas_endpoint('getRecentLogs', {'limit': 20})
        if result and result.get('success'):
            logs = result.get('logs', [])
            st.dataframe(logs, use_container_width=True)
    
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
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
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
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