# check_tables.py
from supabase_db import SupabaseDatabase
import streamlit as st

def check_database_tables():
    print("🔍 Checking database tables...")
    print("=" * 60)
    
    db = SupabaseDatabase()
    
    # Check inventory table
    try:
        inventory = db.get_inventory()
        print(f"✅ Inventory table: {len(inventory)} items")
    except Exception as e:
        print(f"❌ Inventory table error: {e}")
    
    # Check usage_logs table
    try:
        response = db.supabase.table("usage_logs").select("id", count="exact").limit(1).execute()
        print(f"✅ Usage logs table exists")
    except Exception as e:
        print(f"❌ Usage logs table error: {e}")
        print("   Run the SQL script to create usage_logs table")
    
    # Check audit_logs table
    try:
        response = db.supabase.table("audit_logs").select("id", count="exact").limit(1).execute()
        print(f"✅ Audit logs table exists")
    except Exception as e:
        print(f"❌ Audit logs table error: {e}")
        print("   Run the SQL script to create audit_logs table")
    
    # Check users table
    try:
        users = db.get_all_users()
        print(f"✅ Users table: {len(users)} users")
    except Exception as e:
        print(f"❌ Users table error: {e}")
    
    print("=" * 60)
    print("📊 Table Check Complete!")

if __name__ == "__main__":
    check_database_tables()
