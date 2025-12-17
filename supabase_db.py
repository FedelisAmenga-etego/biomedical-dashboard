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
        """Get all users from the database"""
        try:
            response = self.supabase.table("users").select("*").execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            st.error(f"Error getting users: {e}")
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
            print(f"=== DEBUG log_usage() START ===")
            print(f"Usage data received: {usage_data}")
            
            # Prepare the data for Supabase
            # Ensure all required fields are present
            log_data = {
                'item_id': usage_data.get('item_id', ''),
                'item_name': usage_data.get('item_name', ''),
                'units_used': int(usage_data.get('units_used', 0)),
                'purpose': usage_data.get('purpose', ''),
                'used_by': usage_data.get('used_by', 'Unknown'),
                'department': usage_data.get('department', ''),
                'notes': usage_data.get('notes', ''),
                'usage_date': datetime.now().isoformat()
            }
            
            # Add user_id if user is provided
            if user and 'username' in user:
                log_data['user_id'] = user['username']
            
            print(f"Log data to insert: {log_data}")
            
            # Insert into usage_logs table
            print("Inserting into usage_logs table...")
            response = self.supabase.table("usage_logs").insert(log_data).execute()
            
            print(f"Response data: {response.data}")
            print(f"Number of records inserted: {len(response.data)}")
            
            if response.data and len(response.data) > 0:
                print("✅ Successfully logged usage!")
                
                # Update inventory quantity if item_id is available
                item_id = usage_data.get('item_id')
                units_used = int(usage_data.get('units_used', 0))
                
                if item_id and units_used > 0:
                    print(f"Updating inventory for item_id: {item_id}")
                    try:
                        # Get current quantity
                        current_response = self.supabase.table("inventory")\
                            .select("quantity")\
                            .eq("item_id", item_id)\
                            .execute()
                        
                        if current_response.data:
                            current_qty = current_response.data[0].get('quantity', 0)
                            new_qty = current_qty - units_used
                            if new_qty < 0:
                                new_qty = 0
                            
                            print(f"Current quantity: {current_qty}, New quantity: {new_qty}")
                            
                            # Update inventory
                            update_response = self.supabase.table("inventory")\
                                .update({"quantity": new_qty})\
                                .eq("item_id", item_id)\
                                .execute()
                            
                            print(f"Inventory updated successfully")
                    except Exception as update_error:
                        print(f"⚠️ Could not update inventory: {update_error}")
            
            print(f"=== DEBUG log_usage() END ===")
            return len(response.data) > 0
            
        except Exception as e:
            print(f"❌❌❌ ERROR in log_usage(): {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
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

    def get_usage_trends(self):
        """Get detailed usage data for trend analysis"""
        try:
            response = self.supabase.table("usage_logs").select("*").execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error getting usage trends: {e}")
            return pd.DataFrame()
    
    def _log_audit_event(self, user: Dict, action_type: str, table_name: str, 
                        record_id: str = None, field_name: str = None,
                        old_value: str = None, new_value: str = None,
                        notes: str = None, ip_address: str = None, 
                        user_agent: str = None):
        """Log an audit event to the audit_logs table."""
        try:
            audit_data = {
                'user_id': user.get('username', 'unknown'),
                'user_name': user.get('full_name', 'Unknown User'),
                'action_type': action_type,
                'table_name': table_name,
                'record_id': record_id,
                'field_name': field_name,
                'old_value': str(old_value) if old_value is not None else None,
                'new_value': str(new_value) if new_value is not None else None,
                'notes': notes,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            response = self.supabase.table("audit_logs").insert(audit_data).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"❌ ERROR in _log_audit_event(): {e}")
            return False

    def add_inventory_item(self, item_data: Dict, user: Dict = None):
        try:
            response = self.supabase.table("inventory").insert(item_data).execute()
    
            if response.data:
                self.log_audit(
                    user=user,
                    action_type="ADD",
                    table_name="inventory",
                    record_id=item_data["item_id"],
                    old_data=None,
                    new_data=item_data
                )
                return True
    
            return False
        except Exception as e:
            print(f"❌ ERROR in add_inventory_item(): {e}")
            return False


    def update_inventory_item(self, item_id: str, updates: Dict, user: Dict = None):
        try:
            # Fetch old record
            old_response = self.supabase.table("inventory") \
                .select("*") \
                .eq("item_id", item_id) \
                .execute()
    
            old_data = old_response.data[0] if old_response.data else {}
    
            # Apply update
            response = self.supabase.table("inventory") \
                .update(updates) \
                .eq("item_id", item_id) \
                .execute()
    
            if response.data:
                self.log_audit(
                    user=user,
                    action_type="UPDATE",
                    table_name="inventory",
                    record_id=item_id,
                    old_data=old_data,
                    new_data=updates
                )
                return True
    
            return False
        except Exception as e:
            print(f"❌ ERROR in update_inventory_item(): {e}")
            return False


    def log_audit(
    self,
    user: dict,
    action_type: str,
    table_name: str,
    record_id: str,
    old_data: dict = None,
    new_data: dict = None,
):
        try:
            audit_entry = {
                "user_id": user.get("username") if user else "system",
                "action_type": action_type,
                "table_name": table_name,
                "record_id": record_id,
                "old_data": old_data,
                "new_data": new_data,
                "timestamp": datetime.now().isoformat()
            }
    
            self.supabase.table("audit_logs").insert(audit_entry).execute()
            return True
        except Exception as e:
            print("❌ Audit log failed:", e)
            return False

    
    def log_usage(self, usage_data: Dict, user: Dict = None, ip_address: str = None, user_agent: str = None):
        """Log item usage with full audit logging."""
        try:
            print(f"=== DEBUG log_usage() START ===")
            print(f"Usage data received: {usage_data}")
    
            # 1. Insert usage log
            log_data = {
                'item_id': usage_data.get('item_id', ''),
                'item_name': usage_data.get('item_name', ''),
                'units_used': int(usage_data.get('units_used', 0)),
                'purpose': usage_data.get('purpose', ''),
                'used_by': usage_data.get('used_by', 'Unknown'),
                'department': usage_data.get('department', ''),
                'notes': usage_data.get('notes', ''),
                'usage_date': datetime.now().isoformat()
            }
    
            if user and 'username' in user:
                log_data['user_id'] = user['username']
    
            response = self.supabase.table("usage_logs").insert(log_data).execute()
    
            if not response.data:
                return False
    
            print("✅ Usage logged successfully")
    
            # 2. Audit usage event
            self.log_audit(
                user=user,
                action_type="USAGE",
                table_name="usage_logs",
                record_id=str(response.data[0].get("id")),
                old_data=None,
                new_data=log_data
            )
    
            # 3. Update inventory + audit stock mutation
            item_id = usage_data.get('item_id')
            units_used = int(usage_data.get('units_used', 0))
    
            if item_id and units_used > 0:
                current_response = self.supabase.table("inventory") \
                    .select("quantity") \
                    .eq("item_id", item_id) \
                    .execute()
    
                if current_response.data:
                    current_qty = current_response.data[0].get('quantity', 0)
                    new_qty = max(current_qty - units_used, 0)
    
                    # Update inventory
                    self.supabase.table("inventory") \
                        .update({"quantity": new_qty}) \
                        .eq("item_id", item_id) \
                        .execute()
    
                    # 4. Audit inventory quantity change (THIS WAS MISSING)
                    self.log_audit(
                        user=user,
                        action_type="INVENTORY_USAGE",
                        table_name="inventory",
                        record_id=item_id,
                        old_data={"quantity": current_qty},
                        new_data={"quantity": new_qty}
                    )
    
            print(f"=== DEBUG log_usage() END ===")
            return True
    
        except Exception as e:
            print(f"❌ ERROR in log_usage(): {e}")
            import traceback
            print(traceback.format_exc())
            return False




