# test_db.py
import streamlit as st
import bcrypt

st.set_page_config(page_title="Database Test", layout="wide")
st.title("🔧 Direct Database Test")

# Get credentials
supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]

st.write(f"**URL:** {supabase_url}")
st.write(f"**Key:** {supabase_key[:20]}...")

# Test connection
if st.button("Test Database Connection"):
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test query
        result = supabase.table("users").select("*").execute()
        
        st.success(f"✅ Connection successful!")
        st.write(f"Found {len(result.data)} users:")
        
        for user in result.data:
            with st.expander(f"User: {user['username']}"):
                st.write(f"Full Name: {user.get('full_name')}")
                st.write(f"Role: {user.get('role')}")
                st.write(f"Department: {user.get('department')}")
                st.write(f"Password Hash: {user.get('password_hash', 'NO HASH!')[:50]}...")
                st.write(f"Hash Length: {len(user.get('password_hash', ''))}")
                
                # Test bcrypt
                test_pass = st.text_input(f"Test password for {user['username']}", type="password", key=user['username'])
                if test_pass and user.get('password_hash'):
                    try:
                        if bcrypt.checkpw(test_pass.encode('utf-8'), user['password_hash'].encode('utf-8')):
                            st.success("✅ Password matches!")
                        else:
                            st.error("❌ Password does NOT match!")
                    except Exception as e:
                        st.error(f"Bcrypt error: {e}")
                        
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
