# check_users.py
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Check Users", layout="wide")
st.title("👥 Check Database Users")

# Get credentials from secrets
supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]

# Connect to Supabase
supabase = create_client(supabase_url, supabase_key)

if st.button("Check Users Table"):
    try:
        # Get all users
        response = supabase.table("users").select("*").execute()
        
        st.write(f"**Connection successful!**")
        st.write(f"Found {len(response.data)} user(s)")
        
        if response.data:
            for user in response.data:
                with st.expander(f"User: {user['username']}"):
                    st.json(user)
        else:
            st.error("❌ NO USERS FOUND IN DATABASE!")
            st.info("You need to run the SQL script to insert users.")
            
    except Exception as e:
        st.error(f"Error: {e}")
