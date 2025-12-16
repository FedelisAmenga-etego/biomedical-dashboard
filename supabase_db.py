# supabase_db.py - COMPLETE FIXED VERSION
import os
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import bcrypt
from datetime import datetime
from typing import Optional, Dict
import traceback


def get_supabase_creds():
    """
    Get Supabase credentials with proper debugging.
    """
    print("=== DEBUG get_supabase_creds() START ===")
    
    supabase_url = None
    supabase_key = None
    
    # Try all possible locations
    try:
        # Check nested structure (as in main_app.py)
        supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
        supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]
        print("✅ Found credentials in st.secrets['supabase']")
    except Exception as e1:
        print(f"❌ Not in st.secrets['supabase']: {e1}")
        try:
            # Check direct structure
            supabase_url = st.secrets["SUPABASE_URL"]
            supabase_key = st.secrets["SUPABASE_KEY"]
            print("✅ Found credentials in st.secrets directly")
        except Exception as e2:
            print(f"❌ Not in st.secrets directly: {e2}")
            # Check environment
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                print("✅ Found credentials in environment variables")
            else:
                print("❌ Not in environment variables")
    
    # If still not found, raise error
    if not supabase_url or not supabase_key:
        print("❌ ERROR: No Supabase credentials found anywhere!")
        print("Available st.secrets keys:", list(st.secrets.keys()))
        raise ValueError(
            "Supabase credentials missing. "
            "Please check your .streamlit/secrets.toml file. "
            "It should contain:\n"
            "[supabase]\n"
            "SUPABASE_URL = \"https://your-project.supabase.co\"\n"
            "SUPABASE_KEY = \"your-anon-key\""
        )
    
    print(f"✅ URL found: {supabase_url}")
    print(f"✅ Key length: {len(supabase_key)}")
    print(f"✅ Key preview: {supabase_key[:30]}...")
    print("=== DEBUG get_supabase_creds() END ===\n")
    
    return supabase_url, supabase_key


class SupabaseDatabase:
    def __init__(self):
        print("=== DEBUG SupabaseDatabase.__init__() START ===")
        try:
            self.supabase_url, self.supabase_key = get_supabase_creds()
            
            # Create Supabase client
            print("Creating Supabase client...")
            self.supabase: Client = create_client(
                self.supabase_url,
                self.supabase_key
            )
            
            # Test connection
            print("Testing Supabase connection...")
            test_response = self.supabase.table("users").select("*").limit(1).execute()
            print(f"✅ Connected to Supabase successfully!")
            print(f"✅ Test query returned: {len(test_response.data)} rows")
            
        except Exception as e:
            print(f"❌ ERROR in SupabaseDatabase.__init__(): {e}")
            print(traceback.format_exc())
            raise
        print("=== DEBUG SupabaseDatabase.__init__() END ===\n")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password.
        Returns user info dict if successful, None otherwise.
        """
        print(f"=== DEBUG authenticate_user() START: username='{username}' ===")
        
        try:
            # First, check if users table exists and has data
            print("Checking users table...")
            users_response = self.supabase.table("users").select("*").execute()
            print(f"Total users in database: {len(users_response.data)}")
            
            # Find user by username
            print(f"Looking for username: {username}")
            response = self.supabase.table("users")\
                .select("*")\
                .eq("username", username)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                print(f"❌ User '{username}' not found")
                return None
            
            user_data = response.data[0]
            print(f"✅ User found: {user_data.get('username')}")
            
            # Verify password
            stored_hash = user_data.get("password_hash")
            if not stored_hash:
                print("❌ No password hash stored for user")
                return None
            
            # Use bcrypt to verify password
            password_bytes = password.encode('utf-8')
            stored_hash_bytes = stored_hash.encode('utf-8')
            
            if bcrypt.checkpw(password_bytes, stored_hash_bytes):
                print("✅ Password verified successfully!")
                
                # Return user info (without password)
                user_info = {
                    'username': user_data.get('username'),
                    'full_name': user_data.get('full_name', user_data.get('username')),
                    'role': user_data.get('role', 'user'),
                    'department': user_data.get('department', 'Biomedical'),
                    'email': user_data.get('email', '')
                }
                print(f"✅ Returning user info: {user_info}")
                return user_info
            else:
                print("❌ Password verification failed")
                return None
                
        except Exception as e:
            print(f"❌ ERROR in authenticate_user(): {e}")
            print(traceback.format_exc())
            return None
        finally:
            print("=== DEBUG authenticate_user() END ===\n")
    
    # Add other essential methods with debugging
    def get_inventory(self):
        """Get all inventory items."""
        try:
            print("=== DEBUG get_inventory() START ===")
            response = self.supabase.table("inventory").select("*").execute()
            print(f"✅ Retrieved {len(response.data)} inventory items")
            df = pd.DataFrame(response.data)
            
            # Ensure quantity column exists
            if 'total_units' in df.columns and 'quantity' not in df.columns:
                df = df.rename(columns={'total_units': 'quantity'})
            elif 'quantity' not in df.columns and len(df) > 0:
                df['quantity'] = 0
                
            print("=== DEBUG get_inventory() END ===\n")
            return df
        except Exception as e:
            print(f"❌ ERROR in get_inventory(): {e}")
            return pd.DataFrame()
    
    def get_all_users(self):
        """Get all users (admin only)."""
        try:
            response = self.supabase.table("users").select("*").execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"❌ ERROR in get_all_users(): {e}")
            return pd.DataFrame()
    
    def add_inventory_item(self, item_data: Dict, user: Dict = None):
        """Add a new inventory item."""
        try:
            response = self.supabase.table("inventory").insert(item_data).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"❌ ERROR in add_inventory_item(): {e}")
            return False
    
    def update_inventory_item(self, item_id: str, updates: Dict, user: Dict = None):
        """Update an inventory item."""
        try:
            response = self.supabase.table("inventory")\
                .update(updates)\
                .eq("item_id", item_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"❌ ERROR in update_inventory_item(): {e}")
            return False
    
    def log_usage(self, usage_data: Dict, user: Dict = None):
        """Log item usage."""
        try:
            # Add timestamp
            usage_data['usage_date'] = datetime.now().isoformat()
            usage_data['user_id'] = user.get('username') if user else 'unknown'
            
            response = self.supabase.table("usage_logs").insert(usage_data).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"❌ ERROR in log_usage(): {e}")
            return False
    
    def get_usage_stats(self):
        """Get usage statistics."""
        try:
            response = self.supabase.table("usage_logs").select("*").execute()
            df = pd.DataFrame(response.data)
            
            if df.empty:
                return pd.DataFrame()
            
            # Group by item
            stats = df.groupby('item_name').agg({
                'units_used': 'sum',
                'usage_date': 'count'
            }).reset_index()
            
            stats.columns = ['item_name', 'total_units_used', 'usage_count']
            return stats
        except Exception as e:
            print(f"❌ ERROR in get_usage_stats(): {e}")
            return pd.DataFrame()
    
    def get_expired_items(self):
        """Get items that are expired or expiring soon."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            response = self.supabase.table("inventory")\
                .select("*")\
                .not_.is_("expiry_date", "null")\
                .execute()
            
            df = pd.DataFrame(response.data)
            
            if df.empty:
                return df
            
            # Calculate days to expiry
            df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
            df['days_to_expiry'] = (df['expiry_date'] - pd.Timestamp.now()).dt.days
            
            # Ensure quantity column
            if 'total_units' in df.columns and 'quantity' not in df.columns:
                df = df.rename(columns={'total_units': 'quantity'})
                
            return df
        except Exception as e:
            print(f"❌ ERROR in get_expired_items(): {e}")
            return pd.DataFrame()
    
    def create_user(self, user_data: Dict, current_user: Dict = None, ip_address: str = None, user_agent: str = None):
        """Create a new user (admin only)."""
        try:
            # Hash password
            password = user_data.pop('password', '')
            if password:
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
                user_data['password_hash'] = password_hash.decode('utf-8')
            
            # Add timestamps
            user_data['created_at'] = datetime.now().isoformat()
            user_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table("users").insert(user_data).execute()
            return True, f"User '{user_data.get('username')}' created successfully"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def update_user(self, username: str, updates: Dict, current_user: Dict = None, ip_address: str = None, user_agent: str = None):
        """Update user information (admin only)."""
        try:
            # Handle password update
            if 'password' in updates and updates['password']:
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(updates['password'].encode('utf-8'), salt)
                updates['password_hash'] = password_hash.decode('utf-8')
                del updates['password']
            
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table("users")\
                .update(updates)\
                .eq("username", username)\
                .execute()
            
            return True, f"User '{username}' updated successfully"
        except Exception as e:
            return False, f"Error updating user: {str(e)}"
    
    def delete_user(self, username: str, current_user: Dict = None, ip_address: str = None, user_agent: str = None):
        """Delete a user (admin only)."""
        try:
            response = self.supabase.table("users")\
                .delete()\
                .eq("username", username)\
                .execute()
            
            return True, f"User '{username}' deleted successfully"
        except Exception as e:
            return False, f"Error deleting user: {str(e)}"
    
    def get_audit_logs(self, start_date: str = None, end_date: str = None, 
                      user_id: str = None, action_type: str = None, 
                      table_name: str = None, limit: int = 100):
        """Get audit logs."""
        try:
            query = self.supabase.table("audit_logs").select("*")
            
            if start_date:
                query = query.gte("timestamp", start_date)
            if end_date:
                query = query.lte("timestamp", end_date)
            if user_id:
                query = query.eq("user_id", user_id)
            if action_type:
                query = query.eq("action_type", action_type)
            if table_name:
                query = query.eq("table_name", table_name)
            
            query = query.limit(limit).order("timestamp", desc=True)
            response = query.execute()
            
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"❌ ERROR in get_audit_logs(): {e}")
            return pd.DataFrame()
