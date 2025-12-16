# setup_supabase.py
from supabase_db import SupabaseDatabase
from data_processor import DataProcessor
import pandas as pd
import os

def setup_supabase():
    print("Setting up Supabase database...")
    
    db = SupabaseDatabase()
    
    # Check and add sample data if needed
    inventory = db.get_inventory()
    
    if inventory.empty:
        print("Database is empty, checking for sample data...")
        
        # Load sample data
        if os.path.exists("Book2.xlsx"):
            processor = DataProcessor()
            df = processor.load_excel_data("Book2.xlsx")
            
            success_count = 0
            for _, row in df.iterrows():
                item_data = row.to_dict()
                if db.add_inventory_item(item_data):
                    success_count += 1
            
            print(f"✅ Imported {success_count} sample items")
        else:
            print("No sample data found, starting with empty database")
    
    print("✅ Setup complete!")

if __name__ == "__main__":
    setup_supabase()