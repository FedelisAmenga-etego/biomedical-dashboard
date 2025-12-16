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
    
    try:
        # Check nested structure (as in main_app.py)
        supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
        supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]
        print("✅ Found credentials in st.secrets['supabase']")
    except Exception as e:
        print(f"❌ Error getting credentials: {e}")
        print("Available secrets:", list(st.secrets.keys()))
        raise ValueError(f"Failed to get Supabase credentials: {e}")
    
    print(f"✅ URL: {supabase_url}")
    print(f"✅ Key length: {len(supabase_key)}")
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
            
            print("✅ Supabase client created successfully")
            
        except Exception as e:
            print(f"❌ ERROR in SupabaseDatabase.__init__(): {e}")
            print(traceback.format_exc())
            raise
        print("=== DEBUG SupabaseDatabase.__init__() END ===\n")
    
    def authenticate_user(self, username: str, password: str):
        """
        Authenticate a user with username and password.
        Returns user info dict if successful, None otherwise.
        """
        print(f"\n" + "="*60)
        print(f"🔐 AUTHENTICATE_USER called for username: '{username}'")
        print("="*60)
        
        try:
            # 1. First, let's see if we can connect to the database
            print("1. Testing database connection...")
            
            # 2. Get the user from database
            print(f"2. Querying database for user '{username}'...")
            response = self.supabase.table("users")\
                .select("*")\
                .eq("username", username)\
                .execute()
            
            print(f"   Query response data: {response.data}")
            print(f"   Number of users found: {len(response.data)}")
            
            if not response.data or len(response.data) == 0:
                print(f"❌ ERROR: No user found with username '{username}'")
                print("   Available users in database:")
                try:
                    all_users = self.supabase.table("users").select("username").execute()
                    print(f"   {[u['username'] for u in all_users.data]}")
                except:
                    print("   Could not fetch all users")
                return None
            
            user_data = response.data[0]
            print(f"✅ User found in database: {user_data}")
            
            # 3. Check password hash
            stored_hash = user_data.get("password_hash")
            if not stored_hash:
                print("❌ ERROR: User has no password_hash field")
                print(f"   User data keys: {list(user_data.keys())}")
                return None
            
            print(f"3. Found password hash: {stored_hash[:30]}...")
            print(f"   Hash length: {len(stored_hash)}")
            
            # Normalize inputs
            password = password.strip()
            stored_hash = stored_hash.strip()
            
            # Fix bcrypt prefix incompatibility ($2y$ → $2b$)
            if stored_hash.startswith("$2y$"):
                stored_hash = "$2b$" + stored_hash[4:]
            
            # Convert to bytes
            password_bytes = password.encode("utf-8")
            hash_bytes = stored_hash.encode("utf-8")
            
            # Verify password
            print("   Calling bcrypt.checkpw()...")
            if bcrypt.checkpw(password_bytes, hash_bytes):

                print("✅✅✅ PASSWORD VERIFICATION SUCCESSFUL!")
                
                # Return user info
                user_info = {
                    'username': user_data.get('username'),
                    'full_name': user_data.get('full_name', 'User'),
                    'role': user_data.get('role', 'user'),
                    'department': user_data.get('department', 'Biomedical'),
                    'email': user_data.get('email', '')
                }
                print(f"✅ Returning user info: {user_info}")
                return user_info
            else:
                print("❌❌❌ PASSWORD VERIFICATION FAILED!")
                print("   This means:")
                print("   1. Wrong password was entered, OR")
                print("   2. The hash in database doesn't match the password")
                print(f"   Stored hash: {stored_hash}")
                
                # Let's try to generate what the hash SHOULD be
                print("\n   Debug: What hash SHOULD be stored for this password?")
                test_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
                print(f"   Generated test hash: {test_hash.decode('utf-8')[:50]}...")
                
                return None
                
        except Exception as e:
            print(f"❌❌❌ EXCEPTION in authenticate_user: {e}")
            print(traceback.format_exc())
            return None
    
    # Keep other methods as they were
    def get_inventory(self):
        try:
            response = self.supabase.table("inventory").select("*").execute()
            df = pd.DataFrame(response.data)
            
            if 'total_units' in df.columns and 'quantity' not in df.columns:
                df = df.rename(columns={'total_units': 'quantity'})
            elif 'quantity' not in df.columns and len(df) > 0:
                df['quantity'] = 0
                
            return df
        except Exception as e:
            print(f"Error in get_inventory: {e}")
            return pd.DataFrame()
    
    def get_all_users(self):
        try:
            response = self.supabase.table("users").select("*").execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error in get_all_users: {e}")
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


    # In supabase_db.py, add to SupabaseDatabase class
    def get_usage_trends(self):
        """Get detailed usage data for trend analysis"""
        try:
            # Query usage logs from Supabase
            response = self.supabase.table('usage_logs').select('*').execute()
            if response.data:
                return pd.DataFrame(response.data)
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error getting usage trends: {e}")
            return pd.DataFrame()




