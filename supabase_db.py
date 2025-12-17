# supabase_db.py – FINAL STABLE VERSION

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import bcrypt
from datetime import datetime
from typing import Dict
import traceback


# ------------------------------------------------------------------
# Supabase credentials
# ------------------------------------------------------------------
def get_supabase_creds():
    try:
        supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
        supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]
        return supabase_url, supabase_key
    except Exception as e:
        raise RuntimeError(f"Failed to load Supabase credentials: {e}")


# ------------------------------------------------------------------
# Database class
# ------------------------------------------------------------------
class SupabaseDatabase:
    def __init__(self):
        self.supabase_url, self.supabase_key = get_supabase_creds()
        self.supabase: Client = create_client(
            self.supabase_url,
            self.supabase_key
        )

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------
    def authenticate_user(self, username: str, password: str):
        try:
            response = self.supabase.table("users") \
                .select("*") \
                .eq("username", username) \
                .execute()

            if not response.data:
                return None

            user = response.data[0]
            stored_hash = user.get("password_hash", "").strip()

            if stored_hash.startswith("$2y$"):
                stored_hash = "$2b$" + stored_hash[4:]

            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                return {
                    "username": user.get("username"),
                    "full_name": user.get("full_name", "User"),
                    "role": user.get("role", "user"),
                    "department": user.get("department", ""),
                    "email": user.get("email", "")
                }

            return None
        except Exception:
            print(traceback.format_exc())
            return None

    # ------------------------------------------------------------------
    # INVENTORY
    # ------------------------------------------------------------------
    def get_inventory(self):
        try:
            response = self.supabase.table("inventory").select("*").execute()
            return pd.DataFrame(response.data)
        except Exception:
            return pd.DataFrame()

    def add_inventory_item(self, item_data: Dict, user: Dict = None):
        try:
            response = self.supabase.table("inventory").insert(item_data).execute()

            if response.data:
                self._log_audit_event(
                    user=user,
                    action_type="ADD",
                    table_name="inventory",
                    record_id=item_data.get("item_id"),
                    notes="Inventory item added"
                )
                return True

            return False
        except Exception as e:
            print("Add inventory error:", e)
            return False

    def update_inventory_item(self, item_id: str, updates: Dict, user: Dict = None):
        try:
            old = self.supabase.table("inventory") \
                .select("*") \
                .eq("item_id", item_id) \
                .execute()

            old_data = old.data[0] if old.data else {}

            response = self.supabase.table("inventory") \
                .update(updates) \
                .eq("item_id", item_id) \
                .execute()

            if response.data:
                self._log_audit_event(
                    user=user,
                    action_type="UPDATE",
                    table_name="inventory",
                    record_id=item_id,
                    old_value=old_data,
                    new_value=updates,
                    notes="Inventory updated"
                )
                return True

            return False
        except Exception as e:
            print("Update inventory error:", e)
            return False

    # ------------------------------------------------------------------
    # USAGE LOGGING (FIXED & AUDITED)
    # ------------------------------------------------------------------
    def log_usage(self, usage_data: Dict, user: Dict = None,
              ip_address: str = None, user_agent: str = None):
        try:
            item_id = usage_data.get("item_id")
            units_used = int(usage_data.get("units_used", 0))
    
            if not item_id or units_used <= 0:
                return False
    
            # 1. Insert usage log (NO user_id column)
            log_data = {
                "item_id": item_id,
                "item_name": usage_data.get("item_name", ""),
                "units_used": units_used,
                "purpose": usage_data.get("purpose", ""),
                "used_by": usage_data.get("used_by", "Unknown"),
                "department": usage_data.get("department", ""),
                "notes": usage_data.get("notes", ""),
                "usage_date": datetime.now().isoformat()
            }
    
            usage_response = self.supabase.table("usage_logs") \
                .insert(log_data) \
                .execute()
    
            if not usage_response.data:
                return False
    
            # 2. Get current inventory quantity
            inv_response = self.supabase.table("inventory") \
                .select("quantity") \
                .eq("item_id", item_id) \
                .execute()
    
            if not inv_response.data:
                return False
    
            current_qty = inv_response.data[0].get("quantity", 0)
            new_qty = max(current_qty - units_used, 0)
    
            # 3. Update inventory
            self.supabase.table("inventory") \
                .update({"quantity": new_qty}) \
                .eq("item_id", item_id) \
                .execute()
    
            # 4. Audit inventory usage (THIS is where user is recorded)
            self._log_audit_event(
                user=user,
                action_type="INVENTORY_USAGE",
                table_name="inventory",
                record_id=item_id,
                field_name="quantity",
                old_value=current_qty,
                new_value=new_qty,
                notes=f"Used {units_used} units",
                ip_address=ip_address,
                user_agent=user_agent
            )
    
            return True
    
        except Exception as e:
            print("❌ ERROR in log_usage():", e)
            print(traceback.format_exc())
            return False

    # ------------------------------------------------------------------
    # AUDIT LOGGING (SINGLE SOURCE OF TRUTH)
    # ------------------------------------------------------------------
    def _log_audit_event(
        self,
        user: Dict,
        action_type: str,
        table_name: str,
        record_id: str = None,
        field_name: str = None,
        old_value=None,
        new_value=None,
        notes: str = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        try:
            audit_data = {
                "user_id": user.get("username") if user else "system",
                "user_name": user.get("full_name") if user else "System",
                "action_type": action_type,
                "table_name": table_name,
                "record_id": record_id,
                "field_name": field_name,
                "old_value": str(old_value) if old_value is not None else None,
                "new_value": str(new_value) if new_value is not None else None,
                "notes": notes,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.now().isoformat()
            }

            self.supabase.table("audit_logs").insert(audit_data).execute()
            return True
        except Exception as e:
            print("Audit log error:", e)
            return False

    # ------------------------------------------------------------------
    # REPORTING
    # ------------------------------------------------------------------
    def get_audit_logs(self, limit: int = 200):
        try:
            response = self.supabase.table("audit_logs") \
                .select("*") \
                .order("timestamp", desc=True) \
                .limit(limit) \
                .execute()
            return pd.DataFrame(response.data)
        except Exception:
            return pd.DataFrame()

    def get_usage_stats(self):
        try:
            response = self.supabase.table("usage_logs").select("*").execute()
            df = pd.DataFrame(response.data)

            if df.empty:
                return df

            stats = df.groupby("item_name").agg(
                total_units_used=("units_used", "sum"),
                usage_count=("usage_date", "count")
            ).reset_index()

            return stats
        except Exception:
            return pd.DataFrame()

