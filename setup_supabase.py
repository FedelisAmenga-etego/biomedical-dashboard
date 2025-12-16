# setup_supabase.py
from supabase_db import SupabaseDatabase
from data_processor import DataProcessor
import pandas as pd
import os
import bcrypt

def setup_supabase():
    print("🔧 Setting up Biomedical Inventory System with Supabase...")
    print("=" * 60)
    
    # Initialize database
    db = SupabaseDatabase()
    
    # Check if admin exists
    users = db.get_all_users()
    if users.empty:
        print("📝 Creating default admin user...")
        # Hash password for admin
        admin_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        print(f"✅ Admin password hash created")
    
    # Check inventory
    inventory = db.get_inventory()
    print(f"📊 Current inventory items: {len(inventory)}")
    
    # Import sample data if empty
    if inventory.empty and os.path.exists("Book2.xlsx"):
        print("📥 Importing sample data from Book2.xlsx...")
        processor = DataProcessor()
        df = processor.load_excel_data("Book2.xlsx")
        
        success_count = 0
        for _, row in df.iterrows():
            item_data = row.to_dict()
            if db.add_inventory_item(item_data):
                success_count += 1
        
        print(f"✅ Imported {success_count} sample items")
    
    print("=" * 60)
    print("✅ Setup Complete!")
    print("\n🔑 Default Login Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n⚠️  Change admin password immediately after first login!")
    print("=" * 60)

if __name__ == "__main__":
    setup_supabase()
