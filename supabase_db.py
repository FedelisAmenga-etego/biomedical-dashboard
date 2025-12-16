def get_supabase_creds():
    """
    Get Supabase credentials with multiple fallback strategies.
    """
    supabase_url = None
    supabase_key = None
    
    print("=== DEBUG: Starting get_supabase_creds() ===")
    
    # Strategy 1: Check all possible locations
    try:
        print("1. Checking st.secrets['supabase']...")
        supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
        supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]
        print(f"   Found URL: {supabase_url}")
        print(f"   Found KEY: {supabase_key[:30]}...")
        print(f"   Key length: {len(supabase_key)}")
    except Exception as e:
        print(f"   ❌ Not found: {e}")
    
    if not supabase_url or not supabase_key:
        try:
            print("\n2. Checking st.secrets directly...")
            supabase_url = st.secrets["SUPABASE_URL"]
            supabase_key = st.secrets["SUPABASE_KEY"]
            print(f"   Found URL: {supabase_url}")
            print(f"   Found KEY: {supabase_key[:30]}...")
            print(f"   Key length: {len(supabase_key)}")
        except Exception as e:
            print(f"   ❌ Not found: {e}")
    
    if not supabase_url or not supabase_key:
        print("\n3. Checking environment variables...")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            print(f"   Found URL: {supabase_url}")
            print(f"   Found KEY: {supabase_key[:30]}...")
            print(f"   Key length: {len(supabase_key)}")
        else:
            print("   ❌ Not found in environment")
    
    # Final check
    if not supabase_url or not supabase_key:
        print("\n❌ ERROR: No Supabase credentials found!")
        print("Available st.secrets keys:", list(st.secrets.keys()) if hasattr(st.secrets, '__dict__') else "No secrets")
        raise ValueError("Supabase credentials missing")
    
    print(f"\n✅ Final URL: {supabase_url}")
    print(f"✅ Final KEY length: {len(supabase_key)}")
    print(f"✅ Final KEY preview: {supabase_key[:50]}...")
    
    # TEMPORARY: Remove length validation for debugging
    # if len(supabase_key) < 100:
    #     raise ValueError(f"Supabase API key appears invalid or truncated (length: {len(supabase_key)})")
    
    return supabase_url, supabase_key


class SupabaseDatabase:
    def __init__(self):
        self.supabase_url, self.supabase_key = get_supabase_creds()
        
        print(f"\n=== DEBUG: Creating Supabase client ===")
        print(f"URL: {self.supabase_url}")
        print(f"KEY length: {len(self.supabase_key)}")
        print(f"KEY first 50 chars: {self.supabase_key[:50]}")

        # Defensive validation - TEMPORARILY DISABLED
        # if len(self.supabase_key) < 100:
        #     raise ValueError("Supabase API key appears invalid or truncated")

        try:
            self.supabase: Client = create_client(
                self.supabase_url,
                self.supabase_key
            )
            print("✅ Connected to Supabase")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            raise



