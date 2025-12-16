# auth_simple.py - Fixed authentication to work with original credentials
import streamlit as st
from database_simple import SimpleDatabase
import base64
import pandas as pd
import hashlib, binascii, os

class SimpleAuth:
    def __init__(self):
        self.db = SimpleDatabase()
        self.initialize_session_state()
    
    def get_logo_base64(self):
        """Convert logo to base64 for embedding"""
        try:
            with open("logo.png", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded_string}"
        except:
            try:
                with open("nhrc_logo.png", "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                    return f"data:image/png;base64,{encoded_string}"
            except:
                return None
    
    def initialize_session_state(self):
        """Initialize session state variables for authentication"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = {}
    
    def check_auth(self):
        """Check if user is authenticated, redirect to login if not"""
        if st.session_state.authenticated and st.session_state.user_info:
            # Ensure all required fields are present
            user_info = st.session_state.user_info
            if 'full_name' not in user_info:
                user_info['full_name'] = user_info.get('username', 'User').title()
            if 'department' not in user_info:
                user_info['department'] = 'Biomedical'
            if 'role' not in user_info:
                user_info['role'] = 'user'
            return user_info
        
        # Show VC.py style login interface
        self.show_vc_login_interface()
        st.stop()
    
    def show_vc_login_interface(self):
        """Display VC.py style login interface but using original authentication"""
        st.set_page_config(
            page_title="Biomedical Dashboard",
            layout="wide"
        )
        
        # Get logo
        logo_base64 = self.get_logo_base64()
        
        # Header with logo - matching VC.py
        logo_html = ""
        if logo_base64:
            logo_html = f"<img src='{logo_base64}' width='170' style='display:block;margin:0 auto 8px auto;'>"
        else:
            logo_html = "🏥"
        
        st.markdown(
            f"""
            <div style='text-align:center;padding:6px 0 12px 0;background:transparent;'>
                {logo_html}
                <h3 style='margin:0;color:#6A0DAD;'>Navrongo Health Research Centre</h3>
                <h4 style='margin:0;color:#6A0DAD;'>Biomedical Science Department</h4>
                <h6 style='margin:6px 0 0 0;color:#6A0DAD;'>Dr. Victor Asoala – Head of Department</h6>
            </div>
            <hr style='border:1px solid rgba(0,0,0,0.08);margin-bottom:18px;'>
            """,
            unsafe_allow_html=True
        )
        
        # VC.py style sidebar login
        st.sidebar.title("🔐 Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_btn = st.sidebar.button("Login")
        
        if login_btn:
            if not username or not password:
                st.sidebar.error("Please enter both username and password")
            else:
                with st.spinner("🔐 Authenticating..."):
                    # Use the original database authentication
                    user_info = self.db.authenticate_user(username, password)
                    
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        
                        # Ensure user_info has all required fields
                        if 'full_name' not in user_info:
                            user_info['full_name'] = user_info.get('username', 'User').title()
                        if 'department' not in user_info:
                            user_info['department'] = 'Biomedical'
                        if 'role' not in user_info:
                            user_info['role'] = 'user'
                        
                        st.sidebar.success(f"✅ Signed in as {user_info['full_name']}")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Invalid username or password")
        
        # Main content shows info message
        st.info("Please log in from the sidebar to view or manage inventory.")
    
    def authenticate(self, username, password):
        """Authenticate user with username and password"""
        return self.db.authenticate_user(username, password)
    
    def logout(self):
        """Logout user and clear session state"""
        st.session_state.authenticated = False
        st.session_state.user_info = {}
        st.rerun()
    
    def is_admin(self):
        """Check if current user is admin"""
        if st.session_state.authenticated:
            return st.session_state.user_info.get('role') == 'admin'
        return False
    
    def is_manager(self):
        """Check if current user is manager"""
        if st.session_state.authenticated:
            role = st.session_state.user_info.get('role')
            return role in ['admin', 'manager']
        return False