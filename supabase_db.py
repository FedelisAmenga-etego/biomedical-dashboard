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
    Get Supabase credentials.
    Priority:
    1. Streamlit secrets (Cloud)
    2. Environment variables (Local)
    """
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        print("✅ Using Supabase credentials from Streamlit secrets")
    except Exception:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        print("⚠️ Using Supabase credentials from environment variables")

    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase credentials missing. "
            "Set SUPABASE_URL and SUPABASE_KEY in Streamlit secrets or environment."
        )

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
