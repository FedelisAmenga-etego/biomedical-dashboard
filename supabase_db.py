# supabase_db.py
import os
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import bcrypt
from datetime import datetime
from typing import Optional, Dict


def get_supabase_creds():
    """
    Get Supabase credentials with multiple fallback strategies.
    """
    supabase_url = None
    supabase_key = None
    
    # Strategy 1: Nested secrets (as in main_app.py)
    try:
        supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
        supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]
        print("✅ Using Supabase credentials from nested Streamlit secrets")
    except (KeyError, AttributeError):
        pass
    
    # Strategy 2: Direct secrets
    if not supabase_url or not supabase_key:
        try:
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
            if supabase_url and supabase_key:
                print("✅ Using Supabase credentials from direct Streamlit secrets")
        except (KeyError, AttributeError):
            pass
    
    # Strategy 3: Environment variables
    if not supabase_url or not supabase_key:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            print("⚠️ Using Supabase credentials from environment variables")
    
    # Final check
    if not supabase_url or not supabase_key:
        error_msg = "Supabase credentials missing. "
        error_msg += "Set SUPABASE_URL and SUPABASE_KEY in Streamlit secrets or environment."
        error_msg += "\n\nExpected format in .streamlit/secrets.toml:"
        error_msg += "\n[supabase]"
        error_msg += "\nSUPABASE_URL = 'your-project-url'"
        error_msg += "\nSUPABASE_KEY = 'your-anon-key'"
        raise ValueError(error_msg)
    
    # Validate key length
    if len(supabase_key) < 100:
        raise ValueError(f"Supabase API key appears invalid or truncated (length: {len(supabase_key)})")
    
    return supabase_url, supabase_key


class SupabaseDatabase:
    def __init__(self):
        self.supabase_url, self.supabase_key = get_supabase_creds()

        # Defensive validation
        if len(self.supabase_key) < 100:
            raise ValueError("Supabase API key appears invalid or truncated")

        self.supabase: Client = create_client(
            self.supabase_url,
            self.supabase_key
        )

        print("✅ Connected to Supabase")

