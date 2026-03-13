# auth_simple.py - FIXED: session state preserved across reruns
import streamlit as st
from supabase_db import SupabaseDatabase
import base64
import pandas as pd


class SimpleAuth:
    def __init__(self):
        self.db = None  # lazy-loaded
        self.initialize_session_state()
        print("=== DEBUG SimpleAuth.__init__() ===")

    def get_db(self):
        """Create Supabase connection only when needed"""
        print("=== DEBUG SimpleAuth.get_db() ===")
        if self.db is None:
            print("Creating new SupabaseDatabase instance...")
            self.db = SupabaseDatabase()
            print("✅ SupabaseDatabase instance created")
        return self.db

    def get_logo_base64(self):
        try:
            with open("logo.png", "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded}"
        except Exception:
            try:
                with open("nhrc_logo.png", "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode()
                    return f"data:image/png;base64,{encoded}"
            except Exception:
                return None

    def initialize_session_state(self):
        # FIX: Only set defaults if keys are completely absent.
        # Never overwrite existing values — this runs on every rerun via __init__
        # and must not reset a logged-in user's state.
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user_info" not in st.session_state:
            st.session_state.user_info = {}

    def check_auth(self):
        print("=== DEBUG SimpleAuth.check_auth() ===")

        # FIX: Use .get() to safely read session_state.
        # session_state persists across ALL reruns (tab switches, button clicks, st.rerun()).
        # If authenticated is True here, the user is still logged in — do not re-evaluate.
        if st.session_state.get("authenticated") and st.session_state.get("user_info"):
            user_info = st.session_state.user_info
            print(f"User already authenticated: {user_info.get('username')}")

            user_info.setdefault("full_name", user_info.get("username", "User").title())
            user_info.setdefault("department", "Biomedical")
            user_info.setdefault("role", "user")

            return user_info

        # Not authenticated — show login form and stop this rerun.
        # After a successful login, show_login_interface() calls st.rerun(),
        # and the next rerun will hit the early-return above instead.
        print("Showing login interface...")
        self.show_login_interface()
        st.stop()

    def show_login_interface(self):
        print("=== DEBUG SimpleAuth.show_login_interface() ===")
        logo_base64 = self.get_logo_base64()

        logo_html = (
            f"<img src='{logo_base64}' width='170' style='display:block;margin:0 auto 8px auto;'>"
            if logo_base64
            else "🏥"
        )

        st.markdown(
            f"""
            <div style='text-align:center;padding:6px 0 12px 0;'>
                {logo_html}
                <h3 style='margin:0;color:#6A0DAD;'>Navrongo Health Research Centre</h3>
                <h4 style='margin:0;color:#6A0DAD;'>Biomedical Science Department</h4>
                <h6 style='margin-top:6px;color:#6A0DAD;'>Dr. Victor Asoala – Head of Department</h6>
            </div>
            <hr>
            """,
            unsafe_allow_html=True
        )

        st.sidebar.title("🔐 Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_btn = st.sidebar.button("Login")

        if login_btn:
            print(f"Login button clicked for username: {username}")
            if not username or not password:
                st.sidebar.error("Please enter both username and password")
            else:
                with st.spinner("Authenticating..."):
                    print("Calling authenticate_user...")
                    try:
                        db_instance = self.get_db()
                        print(f"Database instance created: {db_instance is not None}")
                        print(f"About to call authenticate_user('{username}', '{password}')")
                        user_info = db_instance.authenticate_user(username, password)
                        print(f"Authentication result: {user_info}")
                    except Exception as e:
                        print(f"❌❌❌ EXCEPTION during authentication: {e}")
                        import traceback
                        traceback.print_exc()
                        user_info = None

                if user_info:
                    # FIX: Set both flags atomically before rerunning
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.sidebar.success(f"Signed in as {user_info['full_name']}")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid username or password. Check logs for details.")

        st.info("Please log in from the sidebar to access the dashboard.")

    def logout(self):
        # FIX: Clear both session state keys cleanly
        st.session_state.authenticated = False
        st.session_state.user_info = {}
        st.rerun()

    def is_admin(self):
        return (
            st.session_state.get("authenticated")
            and st.session_state.user_info.get("role") == "admin"
        )

    def is_manager(self):
        return (
            st.session_state.get("authenticated")
            and st.session_state.user_info.get("role") in ["admin", "manager"]
        )
