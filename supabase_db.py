# supabase_db.py - Supabase PostgreSQL version
import os
from supabase import create_client, Client
import pandas as pd
import bcrypt
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()
def get_supabase_creds():
    """Get credentials from Streamlit secrets or environment."""
    try:
        # Primary: Try to get from Streamlit secrets (for cloud deployment)
        import streamlit as st
        supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
        supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]
        print("✅ Using credentials from Streamlit secrets")
    except (KeyError, FileNotFoundError):
        # Fallback: Try environment variables (for local development)
        print("⚠️  Streamlit secrets not found, checking environment variables...")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase credentials not found. "
            "Please set SUPABASE_URL and SUPABASE_KEY in Streamlit Cloud Secrets "
            "or in a local .env file."
        )
    return supabase_url, supabase_key

class SupabaseDatabase:
    def __init__(self):
        self.supabase_url, self.supabase_key = get_supabase_creds() 
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Key must be set in environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        print("✅ Connected to Supabase")
    
    # ========== USER MANAGEMENT ==========
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user"""
        try:
            response = self.supabase.table('users')\
                .select('*')\
                .eq('username', username)\
                .execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return {
                        'username': user['username'],
                        'full_name': user['full_name'],
                        'role': user['role'],
                        'department': user['department']
                    }
        except Exception as e:
            print(f"Authentication error: {e}")
        
        return None
    
    def get_all_users(self) -> pd.DataFrame:
        """Get all users"""
        try:
            response = self.supabase.table('users')\
                .select('*')\
                .execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error getting users: {e}")
            return pd.DataFrame()
    
    def create_user(self, user_data: Dict, current_user=None) -> tuple:
        """Create a new user"""
        try:
            # Check if user exists
            response = self.supabase.table('users')\
                .select('username')\
                .eq('username', user_data['username'])\
                .execute()
            
            if response.data:
                return False, "Username already exists"
            
            # Hash password
            password_hash = bcrypt.hashpw(
                user_data['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Insert user
            self.supabase.table('users').insert({
                'username': user_data['username'],
                'password_hash': password_hash,
                'full_name': user_data['full_name'],
                'role': user_data.get('role', 'user'),
                'department': user_data.get('department', 'Biomedical')
            }).execute()
            
            # Log audit if current_user provided
            if current_user:
                self.log_audit_event({
                    'user_id': current_user.get('username', 'system'),
                    'user_name': current_user.get('full_name', 'System'),
                    'action_type': 'USER_CREATE',
                    'table_name': 'users',
                    'record_id': user_data['username'],
                    'notes': f'Created new user: {user_data["username"]}'
                })
            
            return True, "User created successfully"
            
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    # ========== INVENTORY MANAGEMENT ==========
    
    def get_inventory(self) -> pd.DataFrame:
        """Get all inventory items"""
        try:
            response = self.supabase.table('inventory')\
                .select('*')\
                .neq('status', 'Deleted')\
                .order('item_name')\
                .execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error getting inventory: {e}")
            return pd.DataFrame()
    
    def add_inventory_item(self, item_data: Dict, current_user=None) -> bool:
        """Add new inventory item"""
        try:
            # Insert item
            response = self.supabase.table('inventory').insert({
                'item_id': item_data['item_id'],
                'item_name': item_data['item_name'],
                'category': item_data['category'],
                'quantity': item_data['quantity'],
                'unit': item_data.get('unit', 'Units'),
                'expiry_date': item_data.get('expiry_date'),
                'storage_location': item_data.get('storage_location', 'Main Store'),
                'supplier': item_data.get('supplier', 'Standard Supplier'),
                'reorder_level': item_data.get('reorder_level', 50),
                'notes': item_data.get('notes', ''),
                'status': 'Active'
            }).execute()
            
            # Log audit
            if current_user:
                self.log_audit_event({
                    'user_id': current_user.get('username', 'system'),
                    'user_name': current_user.get('full_name', 'System'),
                    'action_type': 'CREATE',
                    'table_name': 'inventory',
                    'record_id': item_data['item_id'],
                    'notes': f'Added new item: {item_data["item_name"]}'
                })
            
            return True
            
        except Exception as e:
            print(f"Error adding item: {e}")
            return False
    
    def update_inventory_item(self, item_id: str, updates: Dict, current_user=None) -> bool:
        """Update inventory item"""
        try:
            # Get old values
            response = self.supabase.table('inventory')\
                .select('*')\
                .eq('item_id', item_id)\
                .execute()
            
            old_item = response.data[0] if response.data else None
            
            # Update item
            self.supabase.table('inventory')\
                .update({**updates, 'last_updated': 'now()'})\
                .eq('item_id', item_id)\
                .execute()
            
            # Log audit for each changed field
            if current_user and old_item:
                for field, new_value in updates.items():
                    old_value = old_item.get(field)
                    if old_value != new_value:
                        self.log_audit_event({
                            'user_id': current_user.get('username', 'system'),
                            'user_name': current_user.get('full_name', 'System'),
                            'action_type': 'UPDATE',
                            'table_name': 'inventory',
                            'record_id': item_id,
                            'field_name': field,
                            'old_value': str(old_value) if old_value else None,
                            'new_value': str(new_value) if new_value else None,
                            'notes': f'Updated {field} for item {item_id}'
                        })
            
            return True
            
        except Exception as e:
            print(f"Error updating item: {e}")
            return False
    
    # ========== USAGE LOGGING ==========
    
    def log_usage(self, usage_data: Dict, current_user=None) -> bool:
        """Log item usage"""
        try:
            # Insert usage log
            self.supabase.table('usage_logs').insert({
                'item_id': usage_data['item_id'],
                'item_name': usage_data['item_name'],
                'units_used': usage_data['units_used'],
                'purpose': usage_data.get('purpose', ''),
                'used_by': usage_data['used_by'],
                'department': usage_data.get('department', ''),
                'notes': usage_data.get('notes', '')
            }).execute()
            
            # Update inventory quantity
            self.supabase.rpc('decrement_inventory', {
                'item_id_val': usage_data['item_id'],
                'decrement_val': usage_data['units_used']
            }).execute()
            
            # Log audit
            if current_user:
                self.log_audit_event({
                    'user_id': current_user.get('username', 'system'),
                    'user_name': current_user.get('full_name', 'System'),
                    'action_type': 'USAGE',
                    'table_name': 'inventory',
                    'record_id': usage_data['item_id'],
                    'notes': f'Used {usage_data["units_used"]} units of {usage_data["item_name"]}'
                })
            
            return True
            
        except Exception as e:
            print(f"Error logging usage: {e}")
            return False
    
    def get_usage_stats(self) -> pd.DataFrame:
        """Get usage statistics"""
        try:
            # Create a PostgreSQL function in Supabase or use query
            query = '''
                SELECT 
                    item_name,
                    SUM(units_used) as total_units_used,
                    COUNT(*) as usage_count,
                    MAX(usage_date) as last_used
                FROM usage_logs
                GROUP BY item_name
                ORDER BY total_units_used DESC
            '''
            
            # For Supabase, you can use this approach
            response = self.supabase.table('usage_logs')\
                .select('item_name, units_used, usage_date')\
                .execute()
            
            df = pd.DataFrame(response.data)
            if not df.empty:
                stats = df.groupby('item_name').agg({
                    'units_used': 'sum',
                    'usage_date': ['count', 'max']
                }).reset_index()
                
                stats.columns = ['item_name', 'total_units_used', 'usage_count', 'last_used']
                return stats
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error getting usage stats: {e}")
            return pd.DataFrame()
    
    # ========== AUDIT LOGGING ==========
    
    def log_audit_event(self, audit_data: Dict) -> bool:
        """Log an audit event"""
        try:
            self.supabase.table('audit_logs').insert({
                'user_id': audit_data.get('user_id', 'system'),
                'user_name': audit_data.get('user_name', 'System'),
                'action_type': audit_data.get('action_type', 'UNKNOWN'),
                'table_name': audit_data.get('table_name', 'unknown'),
                'record_id': audit_data.get('record_id', 'unknown'),
                'field_name': audit_data.get('field_name'),
                'old_value': audit_data.get('old_value'),
                'new_value': audit_data.get('new_value'),
                'ip_address': audit_data.get('ip_address'),
                'user_agent': audit_data.get('user_agent'),
                'notes': audit_data.get('notes', '')
            }).execute()
            
            return True
            
        except Exception as e:
            print(f"Error logging audit: {e}")
            return False
    
    def get_audit_logs(self, limit=100) -> pd.DataFrame:
        """Get audit logs"""
        try:
            response = self.supabase.table('audit_logs')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return pd.DataFrame()
    
    # ========== EXPIRY MANAGEMENT ==========
    
    def get_expired_items(self) -> pd.DataFrame:
        """Get expired or expiring items"""
        try:
            response = self.supabase.table('inventory')\
                .select('*')\
                .not_.is_('expiry_date', 'null')\
                .eq('status', 'Active')\
                .order('expiry_date')\
                .execute()
            
            df = pd.DataFrame(response.data)
            if not df.empty and 'expiry_date' in df.columns:
                df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
                df['days_to_expiry'] = (df['expiry_date'] - pd.Timestamp.now()).dt.days
            
            return df
            
        except Exception as e:
            print(f"Error getting expired items: {e}")
            return pd.DataFrame()
    
    # ========== OTHER METHODS ==========
    
    def update_user(self, username: str, updates: Dict, current_user=None) -> tuple:
        """Update user information"""
        try:
            if 'password' in updates and updates['password']:
                password_hash = bcrypt.hashpw(
                    updates['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                updates['password_hash'] = password_hash
                del updates['password']
            
            self.supabase.table('users')\
                .update(updates)\
                .eq('username', username)\
                .execute()
            
            # Log audit
            if current_user:
                self.log_audit_event({
                    'user_id': current_user.get('username', 'system'),
                    'user_name': current_user.get('full_name', 'System'),
                    'action_type': 'USER_UPDATE',
                    'table_name': 'users',
                    'record_id': username,
                    'notes': f'Updated user: {username}'
                })
            
            return True, "User updated successfully"
            
        except Exception as e:
            return False, f"Error updating user: {str(e)}"
    
    def delete_user(self, username: str, current_user=None) -> tuple:
        """Delete a user"""
        if username == 'admin':
            return False, "Cannot delete admin user"
        
        try:
            self.supabase.table('users')\
                .delete()\
                .eq('username', username)\
                .execute()
            
            # Log audit
            if current_user:
                self.log_audit_event({
                    'user_id': current_user.get('username', 'system'),
                    'user_name': current_user.get('full_name', 'System'),
                    'action_type': 'USER_DELETE',
                    'table_name': 'users',
                    'record_id': username,
                    'notes': f'Deleted user: {username}'
                })
            
            return True, "User deleted successfully"
            
        except Exception as e:

            return False, f"Error deleting user: {str(e)}"
