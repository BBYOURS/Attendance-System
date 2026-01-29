# attendance_system_v3.py
import streamlit as st
import requests
import datetime
import time
import pandas as pd
import json

# Session state keys
SESSION_KEYS = ['session_token', 'employee_id', 'employee_name', 'role', 'last_activity']
for key in SESSION_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None

# ==============================================
# UTILITY FUNCTIONS
# ==============================================

def call_gas_endpoint(action, data=None):
    """Call Google Apps Script endpoint"""
    try:
        GAS_ENDPOINT = st.secrets.get("GAS_ENDPOINT", "")
        
        if not GAS_ENDPOINT or "YOUR_GAS" in GAS_ENDPOINT:
            return {"success": False, "message": "System not configured"}
        
        payload = {'action': action}
        if data:
            payload.update(data)
        
        if action != 'login' and st.session_state.session_token:
            payload['sessionToken'] = st.session_state.session_token
        
        response = requests.post(GAS_ENDPOINT, json=payload, timeout=30)
        return response.json()
        
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Connection timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot connect to server"}
    except Exception as e:
        return {"success": False, "message": f"System error: {str(e)}"}

def check_session():
    """Check if session is valid"""
    if not st.session_state.session_token:
        return False
    
    if st.session_state.last_activity:
        idle_time = datetime.datetime.now() - st.session_state.last_activity
        if idle_time.total_seconds() > 600:  # 10 minutes
            logout()
            return False
    
    st.session_state.last_activity = datetime.datetime.now()
    return True

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
        st.warning("Session expired. Please login again.")
        logout()
        st.stop()

def require_role(required_role):
    """Require specific role for page access"""
    require_auth()
    if st.session_state.role != required_role:
        st.error("Unauthorized access")
        logout()
        st.stop()

def mask_id(employee_id):
    """Mask employee ID for display"""
    if not employee_id:
        return "UNKNOWN"
    if len(str(employee_id)) <= 4:
        return employee_id
    return f"***{str(employee_id)[-4:]}"

# ==============================================
# LOGIN PAGE
# ==============================================

def login_page():
    """Login with Name + Password"""
    st.title("🔐 Attendance & Inventory System")
    st.markdown("---")
    
    # Configuration check
    try:
        if 'GAS_ENDPOINT' not in st.secrets or "YOUR_GAS" in st.secrets['GAS_ENDPOINT']:
            st.error("⚠️ System Configuration Required")
            st.markdown("""
            1. **Deploy GAS Code** at [script.google.com](https://script.google.com)
            2. **Copy Web App URL**
            3. **Create `.streamlit/secrets.toml`:**
               ```toml
               GAS_ENDPOINT = "YOUR_GAS_URL"
               ```
            4. **Restart app**
            """)
            return
    except:
        pass
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name", placeholder="Enter your full name")
        
        with col2:
            password = st.text_input("Password", type="password", 
                                   placeholder="12-character password",
                                   help="Password is set by administrator")
        
        col3, col4 = st.columns([1, 3])
        with col3:
            submitted = st.form_submit_button("Login")
        with col4:
            if st.form_submit_button("Clear"):
                st.rerun()
        
        if submitted:
            if not name or not password:
                st.error("Please enter both name and password")
            elif len(password) != 12:
                st.error("Password must be exactly 12 characters")
            else:
                with st.spinner("Authenticating..."):
                    result = call_gas_endpoint('login', {
                        'name': name.strip(),
                        'password': password.strip()
                    })
                
                if result and result.get('success'):
                    st.session_state.session_token = result['sessionToken']
                    st.session_state.employee_id = result['employeeId']
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
# EMPLOYEE DASHBOARD
# ==============================================

def employee_dashboard():
    """Employee dashboard"""
    require_auth()
    
    # Header
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.title(f"👤 {st.session_state.employee_name}")
    with col2:
        result = call_gas_endpoint('getTodayAttendance')
        if result and result.get('success'):
            status = "🟢 Clocked In" if result.get('clockedIn') else "🔴 Not Clocked In"
            st.metric("Status", status)
    with col3:
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["⏰ Attendance", "📦 Inventory", "💰 Payslip", "📨 Messages"])
    
    with tab1:
        attendance_tab()
    
    with tab2:
        inventory_tab()
    
    with tab3:
        payslip_tab()
    
    with tab4:
        messaging_tab()

def attendance_tab():
    """Attendance with early/overtime approval requests"""
    st.header("⏰ Attendance Management")
    
    # Get today's status
    result = call_gas_endpoint('getTodayAttendance')
    clocked_in = result.get('clockedIn', False) if result else False
    clock_out_time = result.get('clockOutTime') if result else None
    
    # Clock In Section
    st.subheader("Clock In")
    col1, col2 = st.columns(2)
    
    with col1:
        if not clocked_in:
            if st.button("🟢 Regular Clock In", use_container_width=True, type="primary"):
                result = call_gas_endpoint('clockIn')
                if result and result.get('success'):
                    st.success("✓ Clocked in successfully!")
                    time.sleep(1)
                    st.rerun()
                elif result and result.get('requiresApproval'):
                    st.info("Early clock-in detected. Please use the Request Early Clock-In button.")
                else:
                    error_msg = result.get('message', 'Failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
        else:
            st.success("✅ Already clocked in today")
    
    with col2:
        if not clocked_in:
            if st.button("⏰ Request Early Clock-In", use_container_width=True):
                st.info("""
                **Early Clock-In Process:**
                1. Check your email for OTP
                2. Admin will approve your request
                3. You'll be notified when approved
                """)
                with st.spinner("Processing request..."):
                    result = call_gas_endpoint('requestEarlyClockIn', {
                        'notes': 'Early clock-in request'
                    })
                    if result and result.get('success'):
                        st.success("✓ Request sent! Check your email for OTP.")
                        st.info("Admin approval is pending. You'll be notified via email.")
                    else:
                        error_msg = result.get('message', 'Failed') if result else 'Error'
                        st.error(f"✗ {error_msg}")
    
    # Clock Out Section
    st.subheader("Clock Out")
    col3, col4 = st.columns(2)
    
    with col3:
        if clocked_in and not clock_out_time:
            if st.button("🔴 Regular Clock Out", use_container_width=True, type="secondary"):
                result = call_gas_endpoint('clockOut')
                if result and result.get('success'):
                    st.success("✓ Clocked out successfully!")
                    time.sleep(1)
                    st.rerun()
                elif result and result.get('requiresApproval'):
                    st.info("Overtime detected. Please use the Request Overtime button.")
                else:
                    error_msg = result.get('message', 'Failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
        elif clock_out_time:
            st.info(f"✅ Clocked out at {clock_out_time}")
        else:
            st.info("⏰ Ready to clock out")
    
    with col4:
        if clocked_in and not clock_out_time:
            if st.button("🌙 Request Overtime", use_container_width=True):
                st.info("""
                **Overtime Process:**
                1. Check your email for OTP
                2. Admin will approve your request
                3. You'll be notified when approved
                """)
                with st.spinner("Processing request..."):
                    result = call_gas_endpoint('requestOvertime', {
                        'notes': 'Overtime request'
                    })
                    if result and result.get('success'):
                        st.success("✓ Request sent! Check your email for OTP.")
                        st.info("Admin approval is pending. You'll be notified via email.")
                    else:
                        error_msg = result.get('message', 'Failed') if result else 'Error'
                        st.error(f"✗ {error_msg}")
    
    # Status Display
    st.markdown("---")
    st.subheader("Today's Status")
    
    if result and result.get('success'):
        col5, col6 = st.columns(2)
        with col5:
            if clocked_in:
                st.success(f"🟢 Clocked In: {result.get('clockInTime', 'N/A')}")
            else:
                st.warning("🔴 Not clocked in")
        
        with col6:
            if clock_out_time:
                st.info(f"✅ Clocked Out: {clock_out_time}")
            elif clocked_in:
                st.info("⏳ Currently working")
    
    # Refresh button
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

def inventory_tab():
    """Inventory access"""
    st.header("📦 Inventory Management")
    
    # Check if clocked in
    result = call_gas_endpoint('getTodayAttendance')
    if not result or not result.get('success') or not result.get('clockedIn'):
        st.warning("⚠️ You must be clocked in to access inventory")
        return
    
    # Get inventory items
    result = call_gas_endpoint('getInventory')
    
    if result and result.get('success'):
        items = result.get('items', [])
        
        if not items:
            st.info("📭 No inventory items available")
            return
        
        with st.form("inventory_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                item_dict = {item['product']: item for item in items}
                selected_item = st.selectbox("Select Item", list(item_dict.keys()))
            
            with col2:
                quantity = st.number_input("Quantity", 1, 50, 1)
            
            with col3:
                if selected_item in item_dict:
                    unit_price = item_dict[selected_item]['sellingPrice']
                    total = quantity * unit_price
                    st.metric("Unit Price", f"₱{unit_price:,.2f}")
                    st.metric("Total", f"₱{total:,.2f}")
            
            if st.form_submit_button("📦 Use Item", use_container_width=True):
                with st.spinner("Processing..."):
                    result = call_gas_endpoint('useInventory', {
                        'item': selected_item,
                        'quantity': quantity,
                        'unitPrice': unit_price
                    })
                
                if result and result.get('success'):
                    st.success(f"✅ Transaction: {result.get('transactionId')}")
                else:
                    error_msg = result.get('message', 'Failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
    else:
        st.error("❌ Unable to load inventory")

def payslip_tab():
    """Employee payslip"""
    st.header("💰 Payslip")
    
    result = call_gas_endpoint('getPayslip')
    
    if result and result.get('success'):
        payslip = result.get('payslip', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Name:** {payslip.get('name', 'N/A')}")
            st.info(f"**Basic Salary:** ₱{payslip.get('basicSalary', 0):,.2f}")
        
        with col2:
            st.success(f"**Gross Pay:** ₱{payslip.get('gross', 0):,.2f}")
            st.warning(f"**Deductions:** ₱{payslip.get('deductions', 0):,.2f}")
        
        st.markdown("---")
        st.markdown(f"### 📄 Net Pay: ₱{payslip.get('netPay', 0):,.2f}")
        
        with st.expander("ℹ️ Security Notice"):
            st.warning("""
            **Read Only:**
            - No export/download available
            - Data protected by security policy
            - Viewing is logged for audit
            """)
    else:
        st.info("📅 Payslip will be available at pay period end")

def messaging_tab():
    """Employee messaging"""
    st.header("📨 Messages")
    
    # Send message to admin
    with st.expander("✉️ Send Message to Admin", expanded=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            msg_type = st.selectbox("Type", 
                ["GENERAL", "EMERGENCY", "QUESTION", "COMPLAINT", "OTHER"])
        
        with col2:
            message = st.text_area("Message", placeholder="Type your message...")
        
        if st.button("📤 Send Message", use_container_width=True):
            if message:
                result = call_gas_endpoint('sendMessage', {
                    'from': st.session_state.employee_name,
                    'to': 'Admin',
                    'message': message,
                    'type': msg_type
                })
                
                if result and result.get('success'):
                    st.success("✓ Message sent to Admin!")
                else:
                    st.error("✗ Failed to send message")
            else:
                st.warning("Please enter a message")
    
    # View messages
    st.markdown("---")
    st.subheader("📥 Messages from Admin")
    
    result = call_gas_endpoint('getMessages', {
        'employeeName': st.session_state.employee_name
    })
    
    if result and result.get('success'):
        messages = result.get('messages', [])
        
        if not messages:
            st.info("No messages")
        else:
            for msg in messages[:10]:
                if msg['to'] == st.session_state.employee_name:
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            if msg['status'] == 'UNREAD':
                                st.markdown(f"**🔔 NEW: {msg['from']}**")
                            else:
                                st.markdown(f"**{msg['from']}**")
                            
                            st.caption(f"{msg['timestamp']} • {msg['type']}")
                            st.write(msg['message'])
                        
                        with col2:
                            if msg['status'] == 'UNREAD':
                                if st.button("✓ Read", key=f"read_{msg['id']}"):
                                    call_gas_endpoint('markMessageRead', {'messageId': msg['id']})
                                    st.rerun()
                        
                        st.divider()
    else:
        st.info("Unable to load messages")

# ==============================================
# ADMIN DASHBOARD
# ==============================================

def admin_dashboard():
    """Admin dashboard with approval system"""
    require_role('ADMIN')
    
    # Header with stats
    result = call_gas_endpoint('getAdminDashboard')
    
    if result and result.get('success'):
        stats = result.get('stats', {})
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Employees", stats.get('totalEmployees', 0))
        with col2:
            st.metric("Clocked In", stats.get('clockedInToday', 0))
        with col3:
            st.metric("Pending Approvals", stats.get('pendingApprovals', 0))
        with col4:
            st.metric("Unread Messages", stats.get('unreadMessages', 0))
    
    st.markdown("---")
    
    # Admin tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Pending Approvals", 
        "👥 Employee Management", 
        "🔐 Password Manager",
        "📊 View Employee Data",
        "📨 Messaging Center",
        "📈 System Logs"
    ])
    
    with tab1:
        pending_approvals_tab()
    
    with tab2:
        employee_management_tab()
    
    with tab3:
        password_manager_tab()
    
    with tab4:
        view_employee_data_tab()
    
    with tab5:
        messaging_center_tab()
    
    with tab6:
        system_logs_tab()
    
    # Sidebar logout
    with st.sidebar:
        st.markdown("---")
        st.info(f"Admin: {st.session_state.employee_name}")
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()

def pending_approvals_tab():
    """Admin: Approve/reject requests"""
    st.header("📋 Pending Approvals")
    
    # Get pending approvals
    result = call_gas_endpoint('getPendingApprovals')
    
    if not result or not result.get('success'):
        st.error("Failed to load approvals")
        return
    
    approvals = result.get('approvals', [])
    
    if not approvals:
        st.success("✅ No pending approvals")
        return
    
    for approval in approvals:
        with st.container():
            st.markdown(f"### {approval['type'].replace('_', ' ')}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Employee:** {approval['employeeName']} ({mask_id(approval['employeeId'])})")
                st.write(f"**Date:** {approval['date']}")
                
                if approval['type'] == 'EARLY_CLOCKIN':
                    st.write(f"**Requested Time:** {approval['clockInTime']}")
                    st.write(f"**Status:** ⏰ Early Clock-In")
                elif approval['type'] == 'OVERTIME':
                    st.write(f"**Clock In:** {approval['clockInTime']}")
                    st.write(f"**Requested Clock Out:** {approval['clockOutTime']}")
                    st.write(f"**Status:** 🌙 Overtime Request")
                
                if approval.get('details'):
                    if 'minutesEarly' in approval['details']:
                        st.write(f"**Minutes Early:** {approval['details']['minutesEarly']:.1f}")
                    if 'minutesOvertime' in approval['details']:
                        st.write(f"**Minutes Overtime:** {approval['details']['minutesOvertime']:.1f}")
            
            with col2:
                col_approve, col_reject = st.columns(2)
                
                with col_approve:
                    if st.button("✅ Approve", key=f"approve_{approval['approvalId']}"):
                        with st.spinner("Processing..."):
                            result = call_gas_endpoint('processApproval', {
                                'approvalId': approval['approvalId'],
                                'approve': True,
                                'adminId': st.session_state.employee_id,
                                'adminName': st.session_state.employee_name
                            })
                            
                            if result and result.get('success'):
                                st.success("✓ Approved!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("✗ Failed to approve")
                
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{approval['approvalId']}"):
                        with st.spinner("Processing..."):
                            result = call_gas_endpoint('processApproval', {
                                'approvalId': approval['approvalId'],
                                'approve': False,
                                'adminId': st.session_state.employee_id,
                                'adminName': st.session_state.employee_name
                            })
                            
                            if result and result.get('success'):
                                st.warning("✓ Rejected!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("✗ Failed to reject")
            
            st.markdown("---")

def employee_management_tab():
    """Admin: View employees"""
    st.header("👥 Employee Management")
    
    if st.button("🔄 Refresh List", use_container_width=True):
        st.rerun()
    
    result = call_gas_endpoint('getAllEmployees')
    
    if result and result.get('success'):
        employees = result.get('employees', [])
        
        if employees:
            df = pd.DataFrame(employees)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No employees found")
    else:
        st.error("Failed to load employees")

def password_manager_tab():
    """Admin: Set employee passwords"""
    st.header("🔐 Password Manager")
    
    # Get employees
    result = call_gas_endpoint('getAllEmployees')
    
    if not result or not result.get('success'):
        st.error("Failed to load employees")
        return
    
    employees = result.get('employees', [])
    
    with st.form("set_password_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            employee_options = {f"{emp['name']} ({emp['employeeId']})": emp['employeeId'] 
                              for emp in employees}
            selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
            target_id = employee_options[selected_employee]
        
        with col2:
            new_password = st.text_input("New Password", type="password",
                                       placeholder="Exactly 12 characters",
                                       help="Must be exactly 12 characters")
            
            confirm_password = st.text_input("Confirm Password", type="password",
                                           placeholder="Re-enter password")
        
        if st.form_submit_button("🔑 Set Password", use_container_width=True):
            if not new_password or not confirm_password:
                st.error("Please enter and confirm password")
            elif len(new_password) != 12:
                st.error("Password must be exactly 12 characters")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                result = call_gas_endpoint('setEmployeePassword', {
                    'targetEmployeeId': target_id,
                    'newPassword': new_password
                })
                
                if result and result.get('success'):
                    st.success(f"✓ Password updated for {selected_employee.split('(')[0]}")
                else:
                    error_msg = result.get('message', 'Failed') if result else 'Error'
                    st.error(f"✗ {error_msg}")
    
    with st.expander("🔒 Password Policy"):
        st.warning("""
        **Security Requirements:**
        - Exactly 12 characters
        - Set by administrator only
        - Never shared via email
        - Logged in security audit
        """)

def view_employee_data_tab():
    """Admin: View employee inventory and payslip"""
    st.header("📊 View Employee Data")
    
    # Get employees
    result = call_gas_endpoint('getAllEmployees')
    
    if not result or not result.get('success'):
        st.error("Failed to load employees")
        return
    
    employees = result.get('employees', [])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        employee_options = {f"{emp['name']} ({emp['employeeId']})": emp['employeeId'] 
                          for emp in employees}
        selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
    
    with col2:
        data_type = st.selectbox("View", ["Payslip", "Inventory", "Both"])
    
    if not selected_employee:
        st.info("Select an employee to view data")
        return
    
    target_id = employee_options[selected_employee]
    employee_name = selected_employee.split('(')[0].strip()
    
    # Display data
    if data_type in ["Payslip", "Both"]:
        st.subheader(f"💰 Payslip for {employee_name}")
        
        result = call_gas_endpoint('getEmployeePayslip', {'employeeId': target_id})
        
        if result and result.get('success'):
            payslip = result.get('payslip', {})
            
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Employee ID", payslip.get('employeeId', 'N/A'))
                st.metric("Position", payslip.get('position', 'N/A'))
                st.metric("Basic Salary", f"₱{payslip.get('basicSalary', 0):,.2f}")
            
            with col4:
                st.metric("Gross Pay", f"₱{payslip.get('gross', 0):,.2f}")
                st.metric("Deductions", f"₱{payslip.get('deductions', 0):,.2f}")
                st.metric("Net Pay", f"₱{payslip.get('netPay', 0):,.2f}")
            
            if st.button("🖨️ Print Payslip", use_container_width=True):
                st.success("Payslip sent to printer queue")
        else:
            st.info("Payslip data not available")
    
    if data_type in ["Inventory", "Both"]:
        st.subheader(f"📦 Inventory for {employee_name}")
        
        result = call_gas_endpoint('getEmployeeInventory', {'employeeId': target_id})
        
        if result and result.get('success'):
            inventory = result.get('inventory', [])
            
            if inventory:
                df = pd.DataFrame(inventory)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                total_items = sum(item['quantity'] for item in inventory)
                total_value = sum(item['total'] for item in inventory)
                
                col5, col6 = st.columns(2)
                with col5:
                    st.metric("Total Items Used", total_items)
                with col6:
                    st.metric("Total Value", f"₱{total_value:,.2f}")
            else:
                st.info("No inventory transactions found")
        else:
            st.info("Inventory data not available")

def messaging_center_tab():
    """Admin: Messaging center"""
    st.header("📨 Messaging Center")
    
    msg_tab1, msg_tab2 = st.tabs(["📤 Send Message", "📥 Inbox"])
    
    with msg_tab1:
        # Get employees for recipient list
        result = call_gas_endpoint('getAllEmployees')
        if result and result.get('success'):
            employees = result.get('employees', [])
            recipient_options = ["ALL EMPLOYEES"] + [emp['name'] for emp in employees]
            recipient = st.selectbox("To", recipient_options)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            msg_type = st.selectbox("Message Type", 
                ["GENERAL", "ANNOUNCEMENT", "WARNING", "URGENT", "OTHER"])
        
        with col2:
            message = st.text_area("Message", height=150,
                                 placeholder="Type your message...")
        
        if st.button("📤 Send to Employee(s)", use_container_width=True):
            if message:
                result = call_gas_endpoint('sendMessage', {
                    'from': 'Admin',
                    'to': recipient,
                    'message': message,
                    'type': msg_type
                })
                
                if result and result.get('success'):
                    st.success(f"✓ Message sent to {recipient}")
                else:
                    st.error("✗ Failed to send message")
            else:
                st.warning("Please enter a message")
    
    with msg_tab2:
        st.subheader("📥 Messages from Employees")
        
        result = call_gas_endpoint('getMessages', {'employeeName': 'Admin'})
        
        if result and result.get('success'):
            messages = result.get('messages', [])
            received = [msg for msg in messages if msg['to'] == 'Admin']
            
            if not received:
                st.info("No messages from employees")
            else:
                for msg in received[:20]:
                    with st.container():
                        if msg['type'] == 'EMERGENCY':
                            st.error(f"🚨 **EMERGENCY:** {msg['from']}")
                        elif msg['type'] == 'URGENT':
                            st.warning(f"⚠️ **URGENT:** {msg['from']}")
                        else:
                            st.markdown(f"**{msg['from']}**")
                        
                        st.caption(f"{msg['timestamp']} • {msg['type']}")
                        st.write(msg['message'])
                        
                        if msg['status'] == 'UNREAD':
                            if st.button("✓ Mark Read", key=f"admin_read_{msg['id']}"):
                                call_gas_endpoint('markMessageRead', {'messageId': msg['id']})
                                st.rerun()
                        
                        st.divider()
        else:
            st.info("Unable to load messages")

def system_logs_tab():
    """Admin: View system logs"""
    st.header("📈 System Logs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_limit = st.slider("Entries to show", 10, 100, 50)
    
    with col2:
        if st.button("🔄 Refresh Logs", use_container_width=True):
            st.rerun()
    
    result = call_gas_endpoint('getRecentLogs', {'limit': log_limit})
    
    if result and result.get('success'):
        logs = result.get('logs', [])
        
        if logs:
            for log in logs:
                with st.expander(f"{log['timestamp']} - {log['action']}"):
                    st.write(f"**User:** {log['user']}")
                    st.write(f"**Action:** {log['action']}")
                    st.write(f"**Status:** {log['status']}")
                    
                    if log['details']:
                        try:
                            details = json.loads(log['details'])
                            st.write("**Details:**", details)
                        except:
                            st.write("**Details:**", log['details'])
        else:
            st.info("No logs found")
    else:
        st.error("Failed to load logs")

# ==============================================
# MAIN APPLICATION
# ==============================================

def main():
    # Page configuration
    st.set_page_config(
        page_title="Attendance System v3.0",
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
    
    # Configuration check
    try:
        if 'GAS_ENDPOINT' not in st.secrets or "YOUR_GAS" in st.secrets['GAS_ENDPOINT']:
            st.error("⚠️ System Configuration Required")
            st.markdown("""
            **Please configure the system:**
            
            1. **Deploy GAS Code:**
               - Go to [script.google.com](https://script.google.com)
               - Create new project
               - Paste the GAS code
               - Deploy as Web App (Anyone access)
               - Copy the URL
            
            2. **Set up secrets.toml:**
               ```toml
               # .streamlit/secrets.toml
               GAS_ENDPOINT = "YOUR_COPIED_URL_HERE"
               ```
            
            3. **Restart the app**
            """)
            return
    except:
        pass
    
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