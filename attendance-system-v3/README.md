# 🏢 Attendance, Inventory & Payroll System v3.0

## 📋 Overview
Complete employee management system with attendance tracking, inventory management, payroll, and real-time messaging. Built with Streamlit frontend and Google Apps Script backend.

## ✨ Features

### 🔐 Authentication
- **Name + Password** login only (admin sets 12-character passwords)
- Session management with auto-logout
- Role-based access (Employee/Admin)

### ⏰ Attendance System
- Regular clock in/out
- Early clock-in detection (>30 mins early requires approval)
- Overtime detection (>15 mins overtime requires approval)
- Separate **Clock Out** and **Log Out** options
- Admin approval via dashboard

### 📦 Inventory Management
- Accessible only when clocked in
- Item validation from pricelist
- Quantity limits (1-50 items/day)
- Transaction ID generation
- Admin can view all employee inventory

### 💰 Payroll System
- Employee view: Read-only payslip
- Admin view: Full payslip with print capability
- Salary data protection
- No export/download (security policy)

### 📨 Messaging System
- **Employee → Admin**: Emergency, OT requests, complaints
- **Admin → Employee**: Announcements, warnings, responses
- Real-time message display
- Message status tracking (Read/Unread)

### 👑 Admin Dashboard
- **Pending Approvals**: Approve/reject early clock-in & overtime
- **Employee Management**: View all employees
- **Password Manager**: Set 12-character passwords
- **Data Viewer**: View employee inventory & payslips
- **Messaging Center**: Send/receive messages
- **System Logs**: Security audit trail

## 🏗️ Architecture
