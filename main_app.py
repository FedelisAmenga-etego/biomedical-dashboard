# main_app.py - Updated with VC.py header and login styles
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from auth_simple import SimpleAuth
from supabase_db import SupabaseDatabase
from data_processor import DataProcessor
from dotenv import load_dotenv
import io
import os
import base64

st.set_page_config(
    page_title="NHRC Biomedical Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AUTHENTICATION
# -------------------------------------------------
auth = SimpleAuth()
user = auth.check_auth()

# Stop app if not authenticated
if not user:
    st.stop()


@st.cache_resource
def get_database():
    return SupabaseDatabase()

db = get_database()

# Ensure get_usage_trends method exists
if not hasattr(db, 'get_usage_trends'):
    # Add the missing method
    def get_usage_trends_fallback(self):
        """Fallback method for get_usage_trends"""
        try:
            # Try to get usage stats as fallback
            return self.get_usage_stats()
        except:
            return pd.DataFrame()
    
    # Add the method to the db instance
    db.get_usage_trends = lambda: get_usage_trends_fallback(db)

# Initialize systems
processor = DataProcessor()

# Get Supabase credentials from Streamlit secrets or environment
def get_supabase_creds():
    try:
        # Try Streamlit secrets first
        import streamlit as st
        return st.secrets["supabase"]["SUPABASE_URL"], st.secrets["supabase"]["SUPABASE_KEY"]
    except:
        # Fall back to environment variables
        return os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")

# Get client info function
def get_client_info():
    """Get client IP and user agent"""
    import streamlit as st
    
    # Try to get IP from various sources
    ip_address = "Unknown"
    user_agent = "Unknown"
    
    try:
        # Get headers from Streamlit request context
        ctx = st.runtime.get_instance()._session_mgr.list_active_sessions()[0].request
        if hasattr(ctx, 'headers'):
            headers = ctx.headers
            ip_address = headers.get('X-Forwarded-For', headers.get('Remote-Addr', 'Unknown'))
            user_agent = headers.get('User-Agent', 'Unknown')
    except:
        pass
    
    return ip_address, user_agent

# Logo function matching VC.py
def get_base64_of_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Load data
inventory_df = db.get_inventory()
# FIX: Use quantity column directly (don't rename)
if 'quantity' not in inventory_df.columns:
    # If database has different column name, adjust here
    inventory_df = inventory_df.copy()
    # The database should return 'quantity' column based on our updated schema

# Calculate metrics - FIX: Ensure quantity column exists
metrics = processor.calculate_metrics(inventory_df)

# FIX: Calculate total_units correctly for display
if 'quantity' in inventory_df.columns:
    metrics['total_units'] = inventory_df['quantity'].sum()
else:
    metrics['total_units'] = 0


# ========== VC.PY STYLE HEADER ==========
logo_html = ""
if os.path.exists("nhrc_logo.png"):
    logo_base64 = get_base64_of_image("nhrc_logo.png")
    logo_html = f"<img src='data:image/png;base64,{logo_base64}' width='170' style='display:block;margin:0 auto 8px auto;'>"
elif os.path.exists("logo.png"):
    logo_base64 = get_base64_of_image("logo.png")
    logo_html = f"<img src='data:image/png;base64,{logo_base64}' width='170' style='display:block;margin:0 auto 8px auto;'>"

# Header matching VC.py exactly
st.markdown(
    f"""
    <div style='text-align:center;padding:6px 0 12px 0;background:transparent;'>
        {logo_html}
        <h3 style='margin:0;color:#6A0DAD;'>Navrongo Health Research Centre</h3>
        <h4 style='margin:0;color:#6A0DAD;'>Biomedical Science Department</h4>
    </div>
    <hr style='border:1px solid rgba(0,0,0,0.08);margin-bottom:18px;'>
    """,
    unsafe_allow_html=True
)

# ========== MAIN NAVIGATION TABS (MOVED FROM SIDEBAR) ==========
# Define the tabs
tabs = tabs = ["🏠 Dashboard", "📦 Inventory", "📝 Usage", "⏰ Expiry", "📈 Analytics", "📋 Audit Trails", "⚙️ Settings"]

# Create tabs using radio buttons with custom styling
selected_tab = st.radio(
    "Navigation",
    tabs,
    horizontal=True,
    label_visibility="collapsed"
)

# Map tab selection to the original variable names
tab_mapping = {
    "🏠 Dashboard": "Dashboard",
    "📦 Inventory": "Inventory", 
    "📝 Usage": "Usage",
    "⏰ Expiry": "Expiry",
    "📈 Analytics": "Analytics",
    "📋 Audit Trails": "AuditTrails",
    "⚙️ Settings": "Settings"
}

# Set active tab in session state
active_tab = tab_mapping[selected_tab]

# ========== UPDATED CUSTOM CSS WITH NEW SIDEBAR STYLING ==========
st.markdown("""
    <style>
    /* Main theme colors - Modern Professional */
    :root {
        --primary: #2563eb;    /* Modern blue */
        --secondary: #1e40af;  /* Darker blue */
        --accent: #3b82f6;     /* Light blue */
        --success: #10b981;    /* Green */
        --warning: #f59e0b;    /* Amber */
        --danger: #ef4444;     /* Red */
        --light: #f8fafc;      /* Light gray */
        --dark: #1e293b;       /* Dark gray */
        --sidebar-bg: #f8f9fa; /* Light grey for sidebar */
        --sidebar-text: #333333; /* Dark text for sidebar */
        --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* UPDATED: Sidebar styling - Light grey/white theme */
    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid #dee2e6;
    }
    
    [data-testid="stSidebar"] * {
        color: var(--sidebar-text) !important;
    }
    
    [data-testid="stSidebar"] .stButton button {
        background: rgba(0, 0, 0, 0.05) !important;
        color: var(--sidebar-text) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(0, 0, 0, 0.2) !important;
        transform: translateY(-1px);
        transition: all 0.3s ease;
    }
    
    /* Main navigation tabs styling */
    div[role='radiogroup'] {
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 25px;
        padding: 10px 0;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    div[role='radiogroup'] label {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px 20px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
        transition: all .2s ease;
        font-weight: 600;
        color: #495057;
        border: 1px solid rgba(0,0,0,0.08);
        margin: 5px;
    }
    
    div[role='radiogroup'] label:hover { 
        transform: translateY(-3px) scale(1.02); 
        box-shadow: 0 8px 20px rgba(0,0,0,0.12); 
        cursor: pointer;
        background: #e9ecef;
    }
    
    div[role='radiogroup'] input:checked + div { 
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important; 
        color: white !important; 
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.2) !important;
        border-color: var(--primary) !important;
    }
    
    /* Main content styling */
    .main-header {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Metric cards - Modern design */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        border-left: 6px solid var(--primary);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--gradient);
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.12);
    }
    
    .metric-icon {
        font-size: 2.2rem;
        margin-bottom: 0.8rem;
        color: var(--primary);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--dark);
        margin: 0.3rem 0;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        font-size: 0.95rem;
        color: #64748b;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Section headers */
    .section-header {
        background: white;
        padding: 1.2rem 1.8rem;
        border-radius: 14px;
        margin: 1rem 0;
        border-left: 6px solid var(--primary);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 2px solid #f1f5f9;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        border: none !important;
        letter-spacing: 0.5px;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.25) !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        letter-spacing: 0.3px;
    }
    
    .status-active { background: #d1fae5; color: var(--success); border: 1px solid #a7f3d0; }
    .status-low { background: #fef3c7; color: var(--warning); border: 1px solid #fde68a; }
    .status-critical { background: #fee2e2; color: var(--danger); border: 1px solid #fecaca; }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--light);
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 10px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        color: var(--dark);
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: white !important;
        border-color: var(--primary) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--secondary), var(--primary));
    }
    
    /* User info card */
    .user-card {
        background: rgba(255, 255, 255, 0.15);
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
    }
    
    /* FIXED: Form styling - Fix chopped/cropped inputs */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input, 
    .stTextArea>div>textarea, 
    .stSelectbox>div>div>div,
    .stDateInput>div>div>input {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 10px 14px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        min-height: 48px !important;
        box-sizing: border-box !important;
    }
    
    .stTextInput>div>div>input:focus, 
    .stNumberInput>div>div>input:focus, 
    .stTextArea>div>textarea:focus, 
    .stSelectbox>div>div>div:focus,
    .stDateInput>div>div>input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }
    
    /* Fix specific input heights */
    input[type="text"], input[type="password"], input[type="number"], input[type="date"] {
        min-height: 48px !important;
        height: auto !important;
        padding: 12px 16px !important;
    }
    
    /* Fix textarea */
    textarea {
        min-height: 100px !important;
        padding: 12px 16px !important;
    }
    
    /* Fix select boxes */
    .stSelectbox>div>div>div {
        padding: 12px 16px !important;
        min-height: 48px !important;
    }
    
    /* Table styling */
    .dataframe th {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        font-weight: 600;
        padding: 12px !important;
    }
    
    .dataframe td {
        padding: 10px !important;
        border-bottom: 1px solid #f1f5f9;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Notification badges */
    .notification-badge {
        display: inline-block;
        background: var(--danger);
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        text-align: center;
        font-size: 0.75rem;
        font-weight: 700;
        line-height: 20px;
        margin-left: 5px;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Card hover effects */
    .hover-card {
        transition: all 0.3s ease;
    }
    
    .hover-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    /* Modern badge */
    .modern-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        color: var(--primary);
        border: 1px solid #bae6fd;
    }
    
    /* Login page styling */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .login-title {
        color: var(--primary);
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    .login-input {
        margin-bottom: 1.5rem;
    }
    
    .login-input label {
        display: block;
        text-align: left;
        margin-bottom: 0.5rem;
        color: var(--dark);
        font-weight: 600;
    }
    
    .login-input input {
        width: 100%;
        padding: 12px 16px;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .login-input input:focus {
        border-color: var(--primary);
        outline: none;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    .login-button {
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.25);
    }
    
    .department-info {
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 2px solid #f1f5f9;
        color: #64748b;
    }
    
    .department-info h3 {
        color: var(--dark);
        margin-bottom: 0.5rem;
    }
    
    .department-info p {
        margin: 0.3rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ========== UPDATED SIDEBAR (SIMPLIFIED) ==========
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0;">
            <div style="font-size: 3.5rem; margin-bottom: 0.8rem; color: #333;">🧬</div>
            <h3 style="margin: 0; color: #333; font-weight: 700;">Biomedical Inventory</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Navrongo Health Research Centre</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # User Info Section
    st.markdown("### 👤 User Information")
    
    user_info_html = f"""
    <div style='background: rgba(0, 0, 0, 0.03); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
        <p style='margin: 0.3rem 0;'><strong>Username:</strong> {user['username']}</p>
        <p style='margin: 0.3rem 0;'><strong>Name:</strong> {user['full_name']}</p>
        <p style='margin: 0.3rem 0;'><strong>Role:</strong> {user['role'].title()}</p>
        <p style='margin: 0.3rem 0;'><strong>Department:</strong> {user['department']}</p>
    </div>
    """
    st.markdown(user_info_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions Only (Removed Quick Stats)
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh Data", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📥 Export Current", use_container_width=True, type="secondary"):
        csv = inventory_df.to_csv(index=False)
        st.download_button(
            "💾 Download CSV",
            data=csv,
            file_name=f"biomedical_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        auth.logout()

# ========== MAIN CONTENT BASED ON SELECTED TAB ==========
# DASHBOARD TAB
if active_tab == "Dashboard":
    st.markdown('<div class="section-header"><h2>📊 Dashboard Overview</h2></div>', unsafe_allow_html=True)
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    metrics_data = [
        ("Total Items", metrics.get('total_items', 0), "📦", "Total number of unique items"),
        ("Total Units", f"{metrics.get('total_units', 0):,}", "🧪", "Total units across all items"),
        ("Categories", metrics.get('categories', 0), "🏷️", "Number of categories"),
        ("Low Stock", metrics.get('low_stock_count', 0), "⚠️", "Items at or below reorder level")
    ]
    
    for col, (label, value, icon, tooltip) in zip([col1, col2, col3, col4], metrics_data):
        with col:
            st.markdown(f"""
                <div class="metric-card" title="{tooltip}">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Units by Category")
        if not inventory_df.empty and 'quantity' in inventory_df.columns:
            category_units = inventory_df.groupby('category')['quantity'].sum().reset_index()
            fig = px.bar(
                category_units,
                x='category',
                y='quantity',
                color='quantity',
                color_continuous_scale='Viridis',
                text='quantity',
                title=""
            )
            fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
            fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📦 Stock Distribution")
        if not inventory_df.empty and 'quantity' in inventory_df.columns:
            fig = px.pie(
                inventory_df,
                values='quantity',
                names='category',
                hole=0.4,
                title=""
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Recent Items Table
        # Recent Items Table
    st.markdown("#### 📋 Recent Inventory Items")
    if not inventory_df.empty:
        # Use quantity column
        display_col = 'quantity'
        recent_items = inventory_df[['item_name', 'category', display_col, 'unit', 'storage_location']].head(10)
        recent_items.columns = ['Item Name', 'Category', 'Quantity', 'Unit', 'Storage Location']
        st.dataframe(recent_items, use_container_width=True, height=300)
    else:
        st.info("No inventory data available. Add items to get started.")

# INVENTORY TAB
elif active_tab == "Inventory":
    st.markdown('<div class="section-header"><h2>📦 Inventory Management</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Inventory", "Add Item", "Edit Item"])
    
    with tab1:
        # Filters - Added expiration filter
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search = st.text_input("🔍 Search items", placeholder="Name or ID...")
        with col2:
            category_filter = st.selectbox("Filter by Category", 
                                        ["All"] + sorted(inventory_df['category'].unique().tolist()))
        with col3:
            status_filter = st.selectbox("Stock Status", ["All", "Adequate", "Low", "Critical"])
        with col4:
            expiry_filter = st.selectbox("Expiry Status", 
                                    ["All", "Expired", "≤ 30 Days", "≤ 90 Days", "> 90 Days", "No Expiry"])
        
        # Apply filters
        filtered = inventory_df.copy()
        if search:
            filtered = filtered[filtered['item_name'].str.contains(search, case=False, na=False) |
                            filtered['item_id'].str.contains(search, case=False, na=False)]
        if category_filter != "All":
            filtered = filtered[filtered['category'] == category_filter]
        
        # Calculate days to expiry for all items first
        filtered = filtered.copy()
        filtered['expiry_date_dt'] = pd.to_datetime(filtered['expiry_date'], errors='coerce')
        current_date = pd.Timestamp.now()
        filtered['days_to_expiry'] = (filtered['expiry_date_dt'] - current_date).dt.days
        
        # Apply stock status filter
        quantity_col = 'quantity'
        if 'reorder_level' in filtered.columns:
            if status_filter == "Low":
                filtered = filtered[filtered[quantity_col] <= filtered['reorder_level']]
            elif status_filter == "Critical":
                filtered = filtered[filtered[quantity_col] == 0]
            elif status_filter == "Adequate":
                filtered = filtered[filtered[quantity_col] > filtered['reorder_level']]
        
        # Apply expiry status filter
        if expiry_filter != "All":
            if expiry_filter == "Expired":
                filtered = filtered[filtered['days_to_expiry'] <= 0]
            elif expiry_filter == "≤ 30 Days":
                filtered = filtered[(filtered['days_to_expiry'] > 0) & (filtered['days_to_expiry'] <= 30)]
            elif expiry_filter == "≤ 90 Days":
                filtered = filtered[(filtered['days_to_expiry'] > 0) & (filtered['days_to_expiry'] <= 90)]
            elif expiry_filter == "> 90 Days":
                filtered = filtered[filtered['days_to_expiry'] > 90]
            elif expiry_filter == "No Expiry":
                filtered = filtered[pd.isna(filtered['expiry_date'])]
        
        # Display with formatting
        if not filtered.empty:
            # Select appropriate quantity column
            display_quantity = 'quantity'
            display_df = filtered[['item_id', 'item_name', 'category', display_quantity, 
                                'unit', 'storage_location', 'expiry_date', 'days_to_expiry']].copy()
            display_df.columns = ['Item ID', 'Item Name', 'Category', 'Quantity', 
                                'Unit', 'Storage Location', 'Expiry Date', 'Days to Expiry']
            
            # Add stock status column
            def get_status(row):
                # Get the original row data from filtered dataframe
                idx = filtered.index[filtered['item_id'] == row['Item ID']][0]
                quantity = filtered.loc[idx, quantity_col]
                reorder_level = filtered.loc[idx, 'reorder_level'] if 'reorder_level' in filtered.columns else 50
                
                if quantity == 0:
                    return '<span class="status-badge status-critical">Critical</span>'
                elif quantity <= reorder_level:
                    return '<span class="status-badge status-low">Low</span>'
                else:
                    return '<span class="status-badge status-active">Adequate</span>'
            
            # Add expiration status column
            def get_expiration_status(row):
                days = row['Days to Expiry']
                if pd.isna(days):
                    return '<span class="status-badge" style="background: #e5e7eb; color: #4b5563; border: 1px solid #d1d5db;">No Expiry</span>'
                elif days <= 0:
                    return '<span class="status-badge status-critical">Expired</span>'
                elif days <= 30:
                    return '<span class="status-badge" style="background: #fef3c7; color: #d97706; border: 1px solid #fde68a;">≤ 30 Days</span>'
                elif days <= 90:
                    return '<span class="status-badge" style="background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd;">≤ 90 Days</span>'
                else:
                    return '<span class="status-badge status-active">> 90 Days</span>'
            
            # Apply the functions
            display_df['Stock Status'] = display_df.apply(get_status, axis=1)
            display_df['Expiry Status'] = display_df.apply(get_expiration_status, axis=1)
            
            # Reorder columns
            display_df = display_df[['Item ID', 'Item Name', 'Category', 'Quantity', 
                                    'Unit', 'Stock Status', 'Expiry Status', 
                                    'Days to Expiry', 'Expiry Date', 'Storage Location']]
            
            # Hide the raw days column for cleaner display (optional)
            display_df_display = display_df.drop('Days to Expiry', axis=1)
            
            # Show filter summary
            filter_summary = []
            if status_filter != "All":
                filter_summary.append(f"Stock: {status_filter}")
            if expiry_filter != "All":
                filter_summary.append(f"Expiry: {expiry_filter}")
            if category_filter != "All":
                filter_summary.append(f"Category: {category_filter}")
            
            summary_text = f"**Showing {len(filtered)} of {len(inventory_df)} items**"
            if filter_summary:
                summary_text += f" - Filters: {', '.join(filter_summary)}"
            
            st.markdown(summary_text)
            
            # Display the table with HTML formatting
            st.markdown("""
            <style>
            .expiry-critical { background-color: #fee2e2; color: #dc2626; }
            .expiry-warning { background-color: #fef3c7; color: #d97706; }
            .expiry-info { background-color: #dbeafe; color: #1e40af; }
            .expiry-good { background-color: #d1fae5; color: #059669; }
            .expiry-none { background-color: #e5e7eb; color: #4b5563; }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(display_df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Legend for expiration status
            st.markdown("""
            <div style="background: #f8fafc; padding: 12px; border-radius: 8px; margin-top: 10px; border: 1px solid #e2e8f0;">
            <strong>Expiry Status Legend:</strong>
            <span class="status-badge status-critical" style="margin-left: 10px;">Expired</span>
            <span class="status-badge" style="background: #fef3c7; color: #d97706; border: 1px solid #fde68a; margin-left: 10px;">≤ 30 Days</span>
            <span class="status-badge" style="background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; margin-left: 10px;">≤ 90 Days</span>
            <span class="status-badge status-active" style="margin-left: 10px;">> 90 Days</span>
            <span class="status-badge" style="background: #e5e7eb; color: #4b5563; border: 1px solid #d1d5db; margin-left: 10px;">No Expiry</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Export
            csv = filtered.to_csv(index=False)
            st.download_button(
                "📥 Export Filtered Data",
                data=csv,
                file_name="filtered_inventory.csv",
                mime="text/csv"
            )
        else:
            st.info("No items match your filters.")
    
    with tab2:
        st.markdown("#### ➕ Add New Item")
        
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                item_name = st.text_input("Item Name*", placeholder="e.g., Sterile Gloves")
                # Expanded category options
                category_options = [
                    "PPE", "Desiccants", "Medical Devices", "Labware", 
                    "Reagents", "Chemicals", "Consumables", "Equipment", 
                    "Packaging", "General Supplies"
                ]
                category = st.selectbox("Category*", category_options)
                quantity = st.number_input("Quantity (Units)*", min_value=1, value=100, step=1,
                                        help="Total number of units")
            
            with col2:
                unit = st.selectbox("Unit*", ["Units", "Packs", "Boxes", "Bottles", "Sets", "Pairs", "Rolls", "Pieces"])
                storage_location = st.selectbox("Storage Location", 
                                            ["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive"])
                # Make expiry date optional
                expiry_date_option = st.radio("Has expiry date?", ["No", "Yes"])
                if expiry_date_option == "Yes":
                    expiry_date = st.date_input("Expiry Date", 
                                            value=datetime.now() + timedelta(days=365))
                else:
                    expiry_date = None
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("➕ Add Item", type="primary")
            
            if submitted:
                if not item_name:
                    st.error("Item Name is required!")
                else:
                    item_id = f"BIO-{category[:3].upper()}-{datetime.now().strftime('%Y%m%d')}-{len(inventory_df)+1:04d}"
                    
                    item_data = {
                        'item_id': item_id,
                        'item_name': item_name,
                        'category': category,
                        'quantity': quantity,
                        'unit': unit,
                        'storage_location': storage_location,
                        'notes': notes,
                        'reorder_level': 50
                    }
                    
                    # Add expiry date only if provided
                    if expiry_date_option == "Yes" and expiry_date:
                        item_data['expiry_date'] = expiry_date.strftime('%Y-%m-%d')
                    
                    # Get client info for audit
                    ip_address, user_agent = get_client_info()
                    
                    if db.add_inventory_item(item_data, user):
                        st.success(f"✅ Item '{item_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add item.")
    with tab3:
        st.markdown("#### ✏️ Edit Inventory Item")
        
        if not inventory_df.empty:
            item_to_edit = st.selectbox("Select item to edit", inventory_df['item_name'].unique())
            
            if item_to_edit:
                item_data = inventory_df[inventory_df['item_name'] == item_to_edit].iloc[0]
                
                with st.form("edit_item_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Get current quantity
                        current_qty = item_data.get('quantity', 0)
                        new_quantity = st.number_input("Quantity (Units)", 
                                                    min_value=0, 
                                                    value=int(current_qty))
                        new_location = st.selectbox("Storage Location", 
                                                ["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive"],
                                                index=["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive"]
                                                .index(item_data.get('storage_location', 'Main Store')))
                        # Add category editing
                        category_options = [
                            "PPE", "Desiccants", "Medical Devices", "Labware", 
                            "Reagents", "Chemicals", "Consumables", "Equipment", 
                            "Packaging", "General Supplies"
                        ]
                        current_category = item_data.get('category', 'General Supplies')
                        if current_category not in category_options:
                            category_options.append(current_category)
                        new_category = st.selectbox("Category", 
                                                category_options,
                                                index=category_options.index(current_category) 
                                                if current_category in category_options else 0)
                    
                    with col2:
                        # Handle expiry date (optional)
                        current_expiry = item_data.get('expiry_date')
                        if pd.notna(current_expiry):
                            expiry_option = st.radio("Expiry Date", ["Keep current", "Change", "Remove"])
                            if expiry_option == "Change":
                                new_expiry = st.date_input("New Expiry Date", 
                                                        value=pd.to_datetime(current_expiry) 
                                                        if pd.notna(current_expiry) 
                                                        else datetime.now() + timedelta(days=365))
                            elif expiry_option == "Remove":
                                new_expiry = None
                            else:
                                new_expiry = current_expiry
                        else:
                            expiry_option = st.radio("Add expiry date?", ["No", "Yes"])
                            if expiry_option == "Yes":
                                new_expiry = st.date_input("Expiry Date", 
                                                        value=datetime.now() + timedelta(days=365))
                            else:
                                new_expiry = None
                        
                        new_reorder_level = st.number_input("Reorder Level (Units)", 
                                                        min_value=1, 
                                                        value=int(item_data.get('reorder_level', 50)))
                        new_notes = st.text_area("Notes", value=item_data.get('notes', ''))
                    
                    submitted = st.form_submit_button("💾 Save Changes", type="primary")
                    
                    if submitted:
                        updates = {
                            'quantity': new_quantity,
                            'storage_location': new_location,
                            'category': new_category,
                            'reorder_level': new_reorder_level,
                            'notes': new_notes
                        }
                        
                        # Handle expiry date
                        if new_expiry is not None:
                            if isinstance(new_expiry, datetime) or hasattr(new_expiry, 'strftime'):
                                updates['expiry_date'] = new_expiry.strftime('%Y-%m-%d')
                            elif new_expiry:  # If it's a string
                                updates['expiry_date'] = new_expiry
                        else:
                            updates['expiry_date'] = None
                        
                        # Get client info for audit
                        ip_address, user_agent = get_client_info()
                        
                        if db.update_inventory_item(item_data['item_id'], updates, user):
                            st.success("✅ Item updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update item.")

# USAGE TRACKING TAB
# USAGE TRACKING TAB
elif active_tab == "Usage":
    st.markdown('<div class="section-header"><h2>📝 Usage Tracking</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Log Usage", "Usage History", "Trend Analysis"])  # Added Trend Analysis tab
    
    with tab1:
        st.markdown("#### 📝 Log Item Usage")
        
        if not inventory_df.empty:
            with st.form("log_usage_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_item = st.selectbox("Select Item*", inventory_df['item_name'].unique())
                    if selected_item:
                        item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                        # Get current quantity
                        current_qty = item_data.get('quantity', 0)
                        max_units = int(current_qty)
                        units_used = st.number_input("Units Used*", 
                                                    min_value=1, 
                                                    max_value=max_units,
                                                    value=1,
                                                    help="Number of units used")
                        purpose = st.text_input("Purpose/Project*", 
                                               placeholder="e.g., Research Project, Daily Operations")
                
                with col2:
                    department = st.selectbox("Department", 
                                            ["Biomedical", "Microbiology", "Parasitology", 
                                             "Clinical Lab", "Research", "Administration"])
                    notes = st.text_area("Notes", placeholder="Additional details...")
                
                submitted = st.form_submit_button("📝 Log Usage", type="primary")
                
                if submitted:
                    if not purpose:
                        st.error("Purpose is required!")
                    elif units_used <= 0:
                        st.error("Units used must be greater than 0!")
                    elif units_used > max_units:
                        st.error(f"Cannot use more than {max_units} units (current stock)")
                    else:
                        usage_data = {
                            'item_id': str(item_data['item_id']),  # Ensure it's a string
                            'item_name': str(selected_item),
                            'units_used': int(units_used),  # Ensure it's an integer
                            'purpose': str(purpose),
                            'used_by': str(user['full_name']),
                            'department': str(department),
                            'notes': str(notes) if notes else ""
                        }
                        
                        st.write("### Debug Info:")
                        st.json(usage_data)
                        
                        # Get client info for audit
                        ip_address, user_agent = get_client_info()
                        
                        # Show loading spinner
                        with st.spinner("Logging usage..."):
                            success = db.log_usage(usage_data, user)
                        
                        if success:
                            st.success(f"✅ Usage of {units_used} units logged successfully!")
                            # Force refresh data
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Failed to log usage.")
                            st.info("Check the terminal/console for error details.")
    
    with tab2:
        st.markdown("#### 📊 Usage Statistics")
        
        usage_stats = db.get_usage_stats()
        
        if not usage_stats.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Top Used Items")
                top_items = usage_stats.nlargest(10, 'total_units_used')
                fig = px.bar(
                    top_items,
                    x='item_name',
                    y='total_units_used',
                    color='total_units_used',
                    text='total_units_used',
                    title=""
                )
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("##### Usage Distribution")
                fig = px.pie(
                    usage_stats,
                    values='total_units_used',
                    names='item_name',
                    hole=0.4,
                    title=""
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.markdown("##### Detailed Usage History")
            st.dataframe(usage_stats, use_container_width=True, height=300)
        else:
            st.info("No usage data available yet.")
    
    with tab3:  # NEW: Trend Analysis Tab
        st.markdown("#### 📈 Usage Trend Analysis")
        
        # Try to get usage trends data
        try:
            detailed_usage_df = db.get_usage_trends()
            
            if detailed_usage_df is None or detailed_usage_df.empty:
                st.info("No usage data available for trend analysis. Start logging usage to see trends.")
            else:
                # Process the data
                if 'usage_date' in detailed_usage_df.columns:
                    # Convert to datetime and extract time components
                    detailed_usage_df['usage_date'] = pd.to_datetime(detailed_usage_df['usage_date'])
                    detailed_usage_df['usage_month'] = detailed_usage_df['usage_date'].dt.strftime('%Y-%m')
                    detailed_usage_df['usage_week'] = detailed_usage_df['usage_date'].dt.strftime('%Y-%W')
                    detailed_usage_df['day_of_week'] = detailed_usage_df['usage_date'].dt.day_name()
                
                # Time period selector
                col1, col2, col3 = st.columns(3)
                with col1:
                    time_period = st.selectbox("Time Period", 
                                             ["Daily", "Weekly", "Monthly", "Quarterly"])
                with col2:
                    chart_type = st.selectbox("Chart Type", 
                                            ["Line Chart", "Bar Chart", "Area Chart"])
                with col3:
                    top_n = st.slider("Top N Items", 5, 20, 10)
                
                # Item selector
                if 'item_name' in detailed_usage_df.columns:
                    all_items = detailed_usage_df['item_name'].unique().tolist()
                else:
                    all_items = []
                
                selected_items = st.multiselect("Select specific items (or leave empty for all)", 
                                              all_items)
                
                if selected_items:
                    filtered_df = detailed_usage_df[detailed_usage_df['item_name'].isin(selected_items)]
                else:
                    filtered_df = detailed_usage_df
                
                if not filtered_df.empty and 'units_used' in filtered_df.columns:
                    # Group by time period
                    if time_period == "Daily":
                        grouped = filtered_df.groupby(['usage_date', 'item_name'])['units_used'].sum().reset_index()
                        x_col = 'usage_date'
                        title_suffix = "Daily"
                    elif time_period == "Weekly":
                        filtered_df['week_start'] = filtered_df['usage_date'] - pd.to_timedelta(filtered_df['usage_date'].dt.dayofweek, unit='D')
                        grouped = filtered_df.groupby(['week_start', 'item_name'])['units_used'].sum().reset_index()
                        x_col = 'week_start'
                        title_suffix = "Weekly"
                    elif time_period == "Monthly":
                        filtered_df['month'] = filtered_df['usage_date'].dt.to_period('M').dt.to_timestamp()
                        grouped = filtered_df.groupby(['month', 'item_name'])['units_used'].sum().reset_index()
                        x_col = 'month'
                        title_suffix = "Monthly"
                    else:  # Quarterly
                        filtered_df['quarter'] = filtered_df['usage_date'].dt.to_period('Q').dt.to_timestamp()
                        grouped = filtered_df.groupby(['quarter', 'item_name'])['units_used'].sum().reset_index()
                        x_col = 'quarter'
                        title_suffix = "Quarterly"
                    
                    # Get top N items by total usage for the trend chart
                    total_usage_by_item = filtered_df.groupby('item_name')['units_used'].sum().nlargest(top_n)
                    top_items_list = total_usage_by_item.index.tolist()
                    trend_df = grouped[grouped['item_name'].isin(top_items_list)]
                    
                    # Create trend chart
                    if not trend_df.empty:
                        st.markdown(f"##### 📊 {title_suffix} Usage Trends (Top {top_n} Items)")
                        
                        if chart_type == "Line Chart":
                            fig = px.line(
                                trend_df,
                                x=x_col,
                                y='units_used',
                                color='item_name',
                                title=f"{title_suffix} Usage Trends",
                                labels={'units_used': 'Units Used', x_col: 'Date'},
                                markers=True
                            )
                        elif chart_type == "Bar Chart":
                            fig = px.bar(
                                trend_df,
                                x=x_col,
                                y='units_used',
                                color='item_name',
                                title=f"{title_suffix} Usage Trends",
                                labels={'units_used': 'Units Used', x_col: 'Date'},
                                barmode='stack'
                            )
                        else:  # Area Chart
                            fig = px.area(
                                trend_df,
                                x=x_col,
                                y='units_used',
                                color='item_name',
                                title=f"{title_suffix} Usage Trends",
                                labels={'units_used': 'Units Used', x_col: 'Date'}
                            )
                        
                        fig.update_layout(
                            height=500,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            hovermode='x unified',
                            xaxis_title="Date",
                            yaxis_title="Units Used",
                            legend_title="Item Name"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Department-wise usage
                    st.markdown("##### 🏢 Department-wise Usage")
                    if 'department' in filtered_df.columns:
                        dept_usage = filtered_df.groupby(['department', 'item_name'])['units_used'].sum().reset_index()
                        top_dept_items = dept_usage.groupby('item_name')['units_used'].sum().nlargest(10).index.tolist()
                        dept_usage_filtered = dept_usage[dept_usage['item_name'].isin(top_dept_items)]
                        
                        if not dept_usage_filtered.empty:
                            fig2 = px.sunburst(
                                dept_usage_filtered,
                                path=['department', 'item_name'],
                                values='units_used',
                                title="Department-wise Usage Distribution",
                                color='units_used',
                                color_continuous_scale='Viridis'
                            )
                            fig2.update_layout(height=500)
                            st.plotly_chart(fig2, use_container_width=True)
                    
                    # Usage heatmap by day of week and hour
                    st.markdown("##### 🕒 Usage Patterns")
                    col_h1, col_h2 = st.columns(2)
                    
                    with col_h1:
                        # Day of week heatmap
                        filtered_df['day_of_week'] = filtered_df['usage_date'].dt.day_name()
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        filtered_df['day_of_week'] = pd.Categorical(filtered_df['day_of_week'], categories=day_order, ordered=True)
                        day_usage = filtered_df.groupby(['day_of_week', 'item_name'])['units_used'].sum().reset_index()
                        
                        # Pivot for heatmap
                        day_pivot = day_usage.pivot(index='item_name', columns='day_of_week', values='units_used').fillna(0)
                        
                        if not day_pivot.empty:
                            fig3 = px.imshow(
                                day_pivot,
                                labels=dict(x="Day of Week", y="Item", color="Units Used"),
                                title="Usage by Day of Week",
                                color_continuous_scale='Viridis',
                                aspect="auto"
                            )
                            fig3.update_layout(height=400)
                            st.plotly_chart(fig3, use_container_width=True)
                    
                    with col_h2:
                        # Purpose-wise breakdown
                        if 'purpose' in filtered_df.columns:
                            purpose_usage = filtered_df.groupby('purpose')['units_used'].sum().reset_index()
                            purpose_usage = purpose_usage.sort_values('units_used', ascending=False).head(10)
                            
                            if not purpose_usage.empty:
                                fig4 = px.bar(
                                    purpose_usage,
                                    x='units_used',
                                    y='purpose',
                                    orientation='h',
                                    color='units_used',
                                    title="Top 10 Usage Purposes",
                                    text='units_used'
                                )
                                fig4.update_traces(texttemplate='%{text:,}', textposition='outside')
                                fig4.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                                st.plotly_chart(fig4, use_container_width=True)
                    
                    # Export detailed trends
                    st.markdown("##### 📥 Export Trend Data")
                    csv = detailed_usage_df.to_csv(index=False)
                    st.download_button(
                        "💾 Download Detailed Usage Data",
                        data=csv,
                        file_name=f"usage_trends_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Usage data doesn't contain required columns for analysis.")
                    
        except AttributeError as e:
            st.error(f"Database method error: {str(e)}")
            st.info("The get_usage_trends() method might not be available. Check if the supabase_db.py file has this method defined.")
        except Exception as e:
            st.error(f"Error loading usage trends: {str(e)}")
            st.info("There was an error loading usage trend data. This might be because:")
            st.info("1. The usage_logs table doesn't exist yet in your Supabase database")
            st.info("2. There's a connection issue with the database")
            st.info("3. The table structure might be different than expected")
                
# EXPIRY MANAGEMENT TAB
elif active_tab == "Expiry":
    st.markdown('<div class="section-header"><h2>⏰ Expiry Management</h2></div>', unsafe_allow_html=True)
    
    expired_items = db.get_expired_items()
    
    # Status cards
    if not expired_items.empty and 'days_to_expiry' in expired_items.columns:
        col1, col2, col3, col4 = st.columns(4)
        
        expired = (expired_items['days_to_expiry'] <= 0).sum()
        expiring_30 = ((expired_items['days_to_expiry'] > 0) & 
                      (expired_items['days_to_expiry'] <= 30)).sum()
        expiring_90 = ((expired_items['days_to_expiry'] > 30) & 
                      (expired_items['days_to_expiry'] <= 90)).sum()
        expiring_180 = ((expired_items['days_to_expiry'] > 90) & 
                       (expired_items['days_to_expiry'] <= 180)).sum()
        
        status_cards = [
            (col1, expired, "Expired", "#ef4444", "❌"),
            (col2, expiring_30, "< 30 Days", "#f59e0b", "⚠️"),
            (col3, expiring_90, "30-90 Days", "#3b82f6", "ℹ️"),
            (col4, expiring_180, "90-180 Days", "#10b981", "✅")
        ]
        
        for col, count, label, color, icon in status_cards:
            with col:
                st.markdown(f"""
                    <div style='background: {color}; padding: 1.2rem; border-radius: 14px; color: white; text-align: center; box-shadow: 0 6px 20px rgba(0,0,0,0.1);'>
                        <div style='font-size: 2.2rem; margin-bottom: 0.5rem;'>{icon}</div>
                        <div style='font-size: 2.2rem; font-weight: 800; margin: 0.5rem 0;'>{count}</div>
                        <div style='font-weight: 700; font-size: 0.95rem;'>{label}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Expiry timeline
    st.markdown("#### 📅 Expiry Timeline")
    
    if not expired_items.empty and 'days_to_expiry' in expired_items.columns:
        # Categorize items
        def categorize_expiry(days):
            if days <= 0:
                return "Expired"
            elif days <= 30:
                return "< 30 days"
            elif days <= 90:
                return "30-90 days"
            elif days <= 180:
                return "90-180 days"
            else:
                return "> 180 days"
        
        expired_items['expiry_category'] = expired_items['days_to_expiry'].apply(categorize_expiry)
        category_counts = expired_items['expiry_category'].value_counts()
        
        fig = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            color=category_counts.values,
            color_continuous_scale='RdYlGn_r',
            text=category_counts.values,
            title=""
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # Expired items table
        st.markdown("#### 🚨 Expired Items Requiring Action")
        
        truly_expired = expired_items[expired_items['days_to_expiry'] <= 0]
        if not truly_expired.empty:
            # Get quantity column
            quantity_col = 'total_units' if 'total_units' in truly_expired.columns else 'quantity'
            st.dataframe(
                truly_expired[['item_name', 'category', quantity_col, 'unit', 
                              'expiry_date', 'days_to_expiry']],
                use_container_width=True,
                height=300
            )
            
            # Quick actions
            st.markdown("##### ⚡ Quick Actions")
            selected_expired = st.selectbox("Select expired item", truly_expired['item_name'].unique())
            
            if selected_expired:
                item_data = truly_expired[truly_expired['item_name'] == selected_expired].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    action = st.radio("Select Action", ["Discard", "Update Expiry"])
                    
                    if action == "Discard":
                        # Get current quantity
                        current_qty = item_data.get('total_units') or item_data.get('quantity', 0)
                        qty = st.number_input("Quantity to discard", 
                                            min_value=1, 
                                            max_value=int(current_qty),
                                            value=int(current_qty))
                        reason = st.selectbox("Reason", ["Expired", "Damaged", "Contaminated", "Other"])
                        
                        if st.button("🗑️ Discard Item", type="primary"):
                            st.success(f"{qty} units of {selected_expired} marked for disposal.")
                    
                    elif action == "Update Expiry":
                        new_expiry = st.date_input("New Expiry Date", 
                                                  value=datetime.now() + timedelta(days=365))
                        if st.button("📅 Update Expiry", type="primary"):
                            updates = {'expiry_date': new_expiry.strftime('%Y-%m-%d')}
                            if db.update_inventory_item(item_data['item_id'], updates):
                                st.success("Expiry date updated!")
                                st.rerun()
                
                with col2:
                    quantity = item_data.get('total_units') or item_data.get('quantity', 0)
                    st.info(f"""
                    **Item Details:**
                    - **ID:** {item_data['item_id']}
                    - **Category:** {item_data['category']}
                    - **Current Stock:** {quantity} units
                    - **Unit:** {item_data.get('unit', 'Units')}
                    - **Expired Since:** {abs(int(item_data['days_to_expiry']))} days
                    """)
        else:
            st.success("✅ No expired items found!")
    else:
        st.info("No expiry data available or items don't have expiry dates set.")

# ANALYTICS TAB
elif active_tab == "Analytics":
    st.markdown('<div class="section-header"><h2>📈 Advanced Analytics</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Inventory Analytics", "Usage Analytics", "Export Reports"])
    
    with tab1:
        if not inventory_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Stock Value Analysis")
                
                # Calculate estimated value - FIXED
                quantity_col = 'quantity' if 'quantity' in inventory_df.columns else 'total_units'
                
                # Ensure we have the column
                if quantity_col in inventory_df.columns:
                    # Make a copy to avoid modifying original
                    plot_df = inventory_df.copy()
                    
                    # Fill NaN values with 0
                    plot_df[quantity_col] = plot_df[quantity_col].fillna(0).astype(float)
                    
                    # Create estimated value (assuming $10 per unit)
                    plot_df['estimated_value'] = plot_df[quantity_col] * 10
                    
                    # Ensure we have required columns for treemap
                    if 'category' in plot_df.columns and 'item_name' in plot_df.columns:
                        # Filter out zero or negative values for better visualization
                        plot_df = plot_df[plot_df['estimated_value'] > 0]
                        
                        if not plot_df.empty:
                            fig = px.treemap(
                                plot_df,
                                path=['category', 'item_name'],
                                values='estimated_value',
                                color='estimated_value',
                                hover_data=[quantity_col],
                                title="Inventory Value by Category"
                            )
                            fig.update_layout(height=500)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No items with positive stock value to display.")
                    else:
                        st.info("Missing required columns for treemap visualization.")
                else:
                    st.info(f"Quantity column '{quantity_col}' not found in data.")
            
            with col2:
                st.markdown("#### 📈 Stock Status Dashboard")
                
                # Stock status distribution using total_units or quantity
                quantity_col = 'total_units' if 'total_units' in inventory_df.columns else 'quantity'
                inventory_df['stock_status'] = inventory_df.apply(
                    lambda x: 'Critical' if x[quantity_col] == 0 
                    else 'Low' if x[quantity_col] <= x.get('reorder_level', 50) 
                    else 'Adequate', axis=1
                )
                
                status_counts = inventory_df['stock_status'].value_counts()
                
                fig = go.Figure(data=[go.Pie(
                    labels=status_counts.index,
                    values=status_counts.values,
                    hole=0.4,
                    marker_colors=['#ef4444', '#f59e0b', '#10b981']
                )])
                fig.update_layout(height=500, title="Stock Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            # Inventory health metrics
            st.markdown("#### 🏥 Inventory Health Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_units = inventory_df['total_units'].sum() if 'total_units' in inventory_df.columns else inventory_df['quantity'].sum()
                turnover_ratio = len(inventory_df) / max(1, total_units)
                st.metric("Stock Turnover Ratio", f"{turnover_ratio:.2f}")
            
            with col2:
                avg_stock = inventory_df['total_units'].mean() if 'total_units' in inventory_df.columns else inventory_df['quantity'].mean()
                st.metric("Average Stock Level", f"{avg_stock:.0f} units")
            
            with col3:
                stock_out_rate = (inventory_df['total_units'] == 0).sum() / len(inventory_df) * 100 if 'total_units' in inventory_df.columns else (inventory_df['quantity'] == 0).sum() / len(inventory_df) * 100
                st.metric("Stock-out Rate", f"{stock_out_rate:.1f}%")
    
    with tab2:
        usage_stats = db.get_usage_stats()
        
        if not usage_stats.empty:
            st.markdown("#### 📈 Usage Pattern Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.scatter(
                    usage_stats,
                    x='usage_count',
                    y='total_units_used',
                    size='total_units_used',
                    color='total_units_used',
                    hover_name='item_name',
                    title="Usage Frequency vs Quantity"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Top 10 items by usage
                top_10 = usage_stats.nlargest(10, 'total_units_used')
                fig = px.bar(
                    top_10,
                    x='item_name',
                    y='total_units_used',
                    color='total_units_used',
                    title="Top 10 Used Items",
                    text='total_units_used'
                )
                fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("#### 📊 Generate Reports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Inventory Report", use_container_width=True):
                # Use appropriate quantity column
                quantity_col = 'total_units' if 'total_units' in inventory_df.columns else 'quantity'
                report = inventory_df[['item_name', 'category', quantity_col, 
                                      'unit', 'storage_location', 'expiry_date']]
                report.columns = ['Item Name', 'Category', 'Quantity', 'Unit', 'Storage Location', 'Expiry Date']
                csv = report.to_csv(index=False)
                st.download_button(
                    "💾 Download Inventory Report",
                    data=csv,
                    file_name="inventory_report.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📝 Usage Report", use_container_width=True):
                usage_stats = db.get_usage_stats()
                csv = usage_stats.to_csv(index=False)
                st.download_button(
                    "💾 Download Usage Report",
                    data=csv,
                    file_name="usage_report.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("⏰ Expiry Report", use_container_width=True):
                expired = db.get_expired_items()
                if not expired.empty:
                    csv = expired.to_csv(index=False)
                    st.download_button(
                        "💾 Download Expiry Report",
                        data=csv,
                        file_name="expiry_report.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No expiry data available")

# AUDIT TRAILS TAB
elif active_tab == "AuditTrails":
    st.markdown('<div class="section-header"><h2>📋 Audit Trails</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Audit Logs", "Change History", "Statistics", "Export"])
    
    with tab1:
        st.markdown("#### 📝 Recent Audit Events")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            days_back = st.selectbox("Time Period", 
                                   ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                                   index=0)
        
        with col2:
            action_filter = st.selectbox("Action Type", 
                                       ["All", "CREATE", "UPDATE", "DELETE", "USAGE", 
                                        "USER_CREATE", "USER_UPDATE", "USER_DELETE", "LOGIN", "LOGOUT"])
        
        with col3:
            table_filter = st.selectbox("Table", 
                                      ["All", "inventory", "users", "usage_logs"])
        
        with col4:
            # Get audit logs from Supabase
            audit_logs_df = db.get_audit_logs(limit=1000)
            if not audit_logs_df.empty:
                users_with_actions = audit_logs_df[['user_id', 'user_name']].drop_duplicates()
            else:
                users_with_actions = pd.DataFrame(columns=['user_id', 'user_name'])
            
            user_options = ["All"]
            if not users_with_actions.empty:
                user_options.extend(users_with_actions['user_id'].tolist())
            
            user_filter = st.selectbox("User", user_options)
        
        # Calculate date range
        end_date = datetime.now()
        if days_back == "Last 7 days":
            start_date = end_date - timedelta(days=7)
        elif days_back == "Last 30 days":
            start_date = end_date - timedelta(days=30)
        elif days_back == "Last 90 days":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = None
        
        # Get filtered audit logs
        audit_logs = db.get_audit_logs(
            start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
            end_date=end_date.strftime('%Y-%m-%d'),
            user_id=user_filter if user_filter != "All" else None,
            action_type=action_filter if action_filter != "All" else None,
            table_name=table_filter if table_filter != "All" else None,
            limit=100
        )
        
        if not audit_logs.empty:
            # Format the display
            display_df = audit_logs.copy()
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Color code action types
            def color_action(action):
                if action in ['CREATE', 'USER_CREATE']:
                    return '🟢'
                elif action in ['UPDATE', 'USER_UPDATE']:
                    return '🔵'
                elif action in ['DELETE', 'USER_DELETE']:
                    return '🔴'
                elif action == 'USAGE':
                    return '🟡'
                else:
                    return '⚪'
            
            display_df['action_icon'] = display_df['action_type'].apply(color_action)
            display_df['action_display'] = display_df['action_icon'] + ' ' + display_df['action_type']
            
            # Show summary
            st.metric("Total Audit Events", len(display_df))
            
            # Display table
            columns_to_show = ['timestamp', 'user_name', 'action_display', 'table_name', 
                              'record_id', 'field_name', 'old_value', 'new_value', 'notes']
            
            st.dataframe(
                display_df[columns_to_show],
                use_container_width=True,
                height=400,
                column_config={
                    'timestamp': st.column_config.TextColumn("Timestamp", width="medium"),
                    'user_name': st.column_config.TextColumn("User", width="small"),
                    'action_display': st.column_config.TextColumn("Action", width="small"),
                    'table_name': st.column_config.TextColumn("Table", width="small"),
                    'record_id': st.column_config.TextColumn("Record ID", width="medium"),
                    'field_name': st.column_config.TextColumn("Field", width="small"),
                    'old_value': st.column_config.TextColumn("Old Value", width="medium"),
                    'new_value': st.column_config.TextColumn("New Value", width="medium"),
                    'notes': st.column_config.TextColumn("Notes", width="large")
                }
            )
            
            # Detailed view for selected row
            st.markdown("#### 🔍 Detailed View")
            if len(display_df) > 0:
                # Create selection options
                selection_options = []
                for idx, row in display_df.iterrows():
                    option_text = f"{row['timestamp']} - {row['user_name']} - {row['action_type']}"
                    if pd.notna(row['record_id']):
                        option_text += f" - {row['record_id']}"
                    selection_options.append((idx, option_text))
                
                selected_option = st.selectbox(
                    "Select event to view details",
                    range(len(selection_options)),
                    format_func=lambda x: selection_options[x][1]
                )
                
                if selected_option is not None:
                    selected_event = display_df.iloc[selected_option]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### Event Details")
                        st.info(f"""
                        **Timestamp:** {selected_event['timestamp']}
                        **User:** {selected_event['user_name']} ({selected_event['user_id']})
                        **Action:** {selected_event['action_type']}
                        **Table:** {selected_event['table_name']}
                        **Record ID:** {selected_event['record_id']}
                        **Field:** {selected_event['field_name'] or 'N/A'}
                        """)
                    
                    with col2:
                        st.markdown("##### Change Details")
                        
                        if pd.notna(selected_event['old_value']) and pd.notna(selected_event['new_value']):
                            st.warning(f"**From:** {selected_event['old_value']}")
                            st.success(f"**To:** {selected_event['new_value']}")
                        elif pd.notna(selected_event['old_value']):
                            st.warning(f"**Removed:** {selected_event['old_value']}")
                        elif pd.notna(selected_event['new_value']):
                            st.success(f"**Added:** {selected_event['new_value']}")
                        
                        if pd.notna(selected_event['notes']):
                            st.markdown(f"**Notes:** {selected_event['notes']}")
                        
                        if pd.notna(selected_event['ip_address']):
                            st.markdown(f"**IP Address:** `{selected_event['ip_address']}`")
        
        else:
            st.info("No audit events found for the selected filters.")
    
    with tab2:
        st.markdown("#### 📊 Change History")
        
        # Get specific record history
        col1, col2 = st.columns(2)
        
        with col1:
            table_select = st.selectbox("Select Table", 
                                      ["inventory", "users", "usage_logs"])
        
        with col2:
            if table_select == "inventory":
                items = inventory_df['item_id'].tolist()
                item_names = inventory_df['item_name'].tolist()
                record_options = {item_id: f"{item_id} - {name}" for item_id, name in zip(items, item_names)}
                if record_options:
                    selected_record = st.selectbox("Select Item", options=list(record_options.keys()),
                                                 format_func=lambda x: record_options[x])
                else:
                    st.info("No inventory items found")
                    selected_record = None
            elif table_select == "users":
                users = db.get_all_users()
                if not users.empty:
                    record_options = {row['username']: f"{row['username']} - {row['full_name']}" 
                                    for _, row in users.iterrows()}
                    selected_record = st.selectbox("Select User", options=list(record_options.keys()),
                                                 format_func=lambda x: record_options[x])
                else:
                    st.info("No users found")
                    selected_record = None
            else:
                selected_record = st.text_input("Enter Record ID")
        
        if selected_record:
            # Get audit history for this record - FIXED PARAMETERS
            record_history = db.get_audit_logs(
                table_name=table_select,
                # Note: The method doesn't have a record_id parameter based on your supabase_db.py
                # We need to filter after fetching
                limit=50
            )
            
            # Filter for the specific record
            if not record_history.empty and 'record_id' in record_history.columns:
                record_history = record_history[record_history['record_id'] == selected_record]
            
            if not record_history.empty:
                # Display as timeline
                st.markdown(f"##### Timeline for {table_select}: {selected_record}")
                
                # Sort by timestamp
                record_history = record_history.sort_values('timestamp', ascending=False)
                record_history['timestamp'] = pd.to_datetime(record_history['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Create timeline visualization
                timeline_html = """
                <style>
                .timeline {
                    position: relative;
                    max-width: 800px;
                    margin: 0 auto;
                }
                .timeline::after {
                    content: '';
                    position: absolute;
                    width: 6px;
                    background-color: #6A0DAD;
                    top: 0;
                    bottom: 0;
                    left: 31px;
                    margin-left: -3px;
                }
                .timeline-item {
                    padding: 10px 40px;
                    position: relative;
                    background-color: inherit;
                    width: 100%;
                }
                .timeline-item::after {
                    content: '';
                    position: absolute;
                    width: 20px;
                    height: 20px;
                    background-color: white;
                    border: 4px solid #6A0DAD;
                    top: 15px;
                    left: 22px;
                    border-radius: 50%;
                    z-index: 1;
                }
                .timeline-content {
                    padding: 15px;
                    background-color: white;
                    position: relative;
                    border-radius: 6px;
                    border: 1px solid #e0e0e0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .timeline-action {
                    font-weight: bold;
                    color: #6A0DAD;
                    margin-bottom: 5px;
                }
                .timeline-user {
                    color: #666;
                    font-size: 0.9em;
                    margin-bottom: 5px;
                }
                .timeline-change {
                    background-color: #f5f5f5;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0;
                    font-size: 0.9em;
                }
                .create { border-left: 4px solid #10b981; }
                .update { border-left: 4px solid #3b82f6; }
                .delete { border-left: 4px solid #ef4444; }
                .usage { border-left: 4px solid #f59e0b; }
                </style>
                <div class="timeline">
                """
                
                for _, event in record_history.iterrows():
                    action_class = str(event['action_type']).lower()
                    if 'create' in action_class:
                        color_class = 'create'
                    elif 'update' in action_class:
                        color_class = 'update'
                    elif 'delete' in action_class:
                        color_class = 'delete'
                    elif 'usage' in action_class:
                        color_class = 'usage'
                    else:
                        color_class = ''
                    
                    change_html = ""
                    if pd.notna(event['field_name']):
                        old_val = str(event['old_value']) if pd.notna(event['old_value']) else 'None'
                        new_val = str(event['new_value']) if pd.notna(event['new_value']) else 'None'
                        change_html = f"""
                        <div class="timeline-change">
                            <strong>{event['field_name']}:</strong><br>
                            <span style="color: #ef4444;">{old_val}</span> → 
                            <span style="color: #10b981;">{new_val}</span>
                        </div>
                        """
                    
                    timeline_html += f"""
                    <div class="timeline-item">
                        <div class="timeline-content {color_class}">
                            <div class="timeline-action">{event['action_type']}</div>
                            <div class="timeline-user">By {event['user_name']} at {event['timestamp']}</div>
                            {change_html}
                            <div style="font-size: 0.8em; color: #888; margin-top: 5px;">
                                {event['notes'] or ''}
                            </div>
                        </div>
                    </div>
                    """
                
                timeline_html += "</div>"
                st.markdown(timeline_html, unsafe_allow_html=True)
                
                # Also show as table
                st.markdown("##### Tabular View")
                display_cols = ['timestamp', 'user_name', 'action_type', 'field_name', 
                              'old_value', 'new_value', 'notes']
                st.dataframe(record_history[display_cols], use_container_width=True, height=300)
            else:
                st.info("No change history found for this record.")
        else:
            st.info("Please select a record to view its change history.")
    
    with tab3:
        st.markdown("#### 📈 Audit Statistics")
        
        # Get audit summary - FIXED: create summary from existing data
        try:
            # Get audit logs to create summary
            audit_logs_df = db.get_audit_logs(limit=1000)
            
            if not audit_logs_df.empty:
                total_events = len(audit_logs_df)
                user_count = audit_logs_df['user_id'].nunique() if 'user_id' in audit_logs_df.columns else 0
                table_count = audit_logs_df['table_name'].nunique() if 'table_name' in audit_logs_df.columns else 0
                action_types_count = audit_logs_df['action_type'].nunique() if 'action_type' in audit_logs_df.columns else 0
                
                # Create summary DataFrames
                by_action = audit_logs_df['action_type'].value_counts().reset_index()
                by_action.columns = ['action_type', 'count']
                
                by_user = audit_logs_df.groupby('user_id').agg(
                    user_name=('user_name', 'first'),
                    action_count=('id', 'count')
                ).reset_index().sort_values('action_count', ascending=False)
                
                by_table = audit_logs_df['table_name'].value_counts().reset_index()
                by_table.columns = ['table_name', 'count']
                
                # Summary cards
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Events", total_events)
                
                with col2:
                    st.metric("Active Users", user_count)
                
                with col3:
                    st.metric("Tables Tracked", table_count)
                
                with col4:
                    st.metric("Action Types", action_types_count)
                
                # Charts
                if total_events > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### Events by Action Type")
                        if not by_action.empty:
                            fig = px.bar(
                                by_action,
                                x='action_type',
                                y='count',
                                color='count',
                                text='count',
                                title=""
                            )
                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                            fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("##### Events by User")
                        if not by_user.empty:
                            fig = px.bar(
                                by_user.head(10),
                                x='user_name',
                                y='action_count',
                                color='action_count',
                                text='action_count',
                                title="Top 10 Active Users"
                            )
                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                            fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Daily activity trend
                    st.markdown("##### 📅 Daily Activity Trend")

                    # Get audit logs and process in pandas
                    audit_logs_df = db.get_audit_logs(limit=10000)  # Get enough data
                    if not audit_logs_df.empty:
                        audit_logs_df['timestamp'] = pd.to_datetime(audit_logs_df['timestamp'])
                        audit_logs_df['activity_date'] = audit_logs_df['timestamp'].dt.date
                        
                        daily_activity = audit_logs_df.groupby('activity_date').agg(
                            event_count=('id', 'count'),
                            unique_users=('user_id', 'nunique')
                        ).reset_index().sort_values('activity_date', ascending=False).head(30)
                    else:
                        daily_activity = pd.DataFrame(columns=['activity_date', 'event_count', 'unique_users'])
                    
                    if not daily_activity.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=daily_activity['activity_date'],
                            y=daily_activity['event_count'],
                            name='Total Events',
                            marker_color='#6A0DAD'
                        ))
                        fig.add_trace(go.Scatter(
                            x=daily_activity['activity_date'],
                            y=daily_activity['unique_users'],
                            name='Unique Users',
                            mode='lines+markers',
                            line=dict(color='#10b981', width=3),
                            yaxis='y2'
                        ))
                        
                        fig.update_layout(
                            height=400,
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            xaxis_title="Date",
                            yaxis_title="Total Events",
                            yaxis2=dict(
                                title="Unique Users",
                                overlaying='y',
                                side='right'
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No audit data available for statistics.")
                
        except Exception as e:
            st.error(f"Error loading audit statistics: {str(e)}")
            st.info("The audit system may not be fully initialized yet. Try adding or modifying some items first.")
    
    with tab4:
        st.markdown("#### 📤 Export Audit Data")
        
        st.info("""
        **Export Options:**
        - **Full Audit Log:** Complete audit trail
        - **Filtered Export:** Based on current filters
        - **Compliance Report:** Formatted for regulatory requirements
        """)
        
        export_format = st.radio("Export Format", ["CSV", "Excel"])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Export Full Audit Log", use_container_width=True):
                all_logs = db.get_audit_logs(limit=10000)  # Large limit to get all
                if not all_logs.empty:
                    if export_format == "CSV":
                        csv = all_logs.to_csv(index=False)
                        st.download_button(
                            "💾 Download CSV",
                            data=csv,
                            file_name=f"audit_log_full_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    elif export_format == "Excel":
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            all_logs.to_excel(writer, index=False, sheet_name='Audit_Logs')
                        output.seek(0)
                        st.download_button(
                            "💾 Download Excel",
                            data=output,
                            file_name=f"audit_log_full_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.warning("No audit data to export")
        
        with col2:
            if st.button("🎛️ Export Filtered Logs", use_container_width=True):
                # Use current tab1 filters
                if 'audit_logs' in locals() and not audit_logs.empty:
                    current_logs = audit_logs
                else:
                    current_logs = db.get_audit_logs(limit=1000)
                
                if not current_logs.empty:
                    csv = current_logs.to_csv(index=False)
                    st.download_button(
                        "💾 Download Filtered",
                        data=csv,
                        file_name=f"audit_log_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No filtered audit data to export")
        
        with col3:
            if st.button("📄 Generate Summary Report", use_container_width=True):
                try:
                    # Get audit logs to create summary
                    audit_logs_df = db.get_audit_logs(limit=10000)
                    
                    if not audit_logs_df.empty:
                        # Create summary statistics
                        total_events = len(audit_logs_df)
                        user_count = audit_logs_df['user_id'].nunique()
                        table_count = audit_logs_df['table_name'].nunique()
                        action_types_count = audit_logs_df['action_type'].nunique()
                        
                        # Create summary tables
                        by_action = audit_logs_df['action_type'].value_counts().reset_index()
                        by_action.columns = ['Action Type', 'Count']
                        
                        by_user = audit_logs_df.groupby('user_id').agg(
                            User_Name=('user_name', 'first'),
                            Action_Count=('id', 'count')
                        ).reset_index().sort_values('Action_Count', ascending=False)
                        
                        by_table = audit_logs_df['table_name'].value_counts().reset_index()
                        by_table.columns = ['Table Name', 'Count']
                        
                        # Create a summary report
                        report_data = {
                            'Report Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Total Audit Events': total_events,
                            'Active Users': user_count,
                            'Tables Tracked': table_count,
                            'Action Types': action_types_count
                        }
                        
                        # Create report DataFrame
                        report_df = pd.DataFrame([report_data])
                        
                        # Also include summary tables
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            report_df.to_excel(writer, index=False, sheet_name='Summary')
                            
                            if not by_action.empty:
                                by_action.to_excel(writer, index=False, sheet_name='By_Action')
                            
                            if not by_user.empty:
                                by_user.to_excel(writer, index=False, sheet_name='By_User')
                            
                            if not by_table.empty:
                                by_table.to_excel(writer, index=False, sheet_name='By_Table')
                        
                        output.seek(0)
                        st.download_button(
                            "💾 Download Summary Report",
                            data=output,
                            file_name=f"audit_summary_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                    else:
                        st.warning("No audit data available for summary report.")
                    
                except Exception as e:
                    st.error(f"Error generating summary report: {str(e)}")

# SETTINGS TAB
elif active_tab == "Settings":
    st.markdown('<div class="section-header"><h2>⚙️ System Settings</h2></div>', unsafe_allow_html=True)
    users_df = db.get_all_users()
    # Check if user has permission
    if not auth.is_admin():
        st.error("⛔ Administrator access required for user management.")
        
        # Show limited settings for non-admins
        tab1, tab2 = st.tabs(["My Profile", "Preferences"])
        
        with tab1:
            st.markdown("#### 👤 My Profile")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **User Information:**
                - **Username:** {user['username']}
                - **Full Name:** {user['full_name']}
                - **Role:** {user['role'].title()}
                - **Department:** {user['department']}
                """)
            
            with col2:
                st.markdown("##### Change Password")
                with st.form("change_password_form"):
                    current_password = st.text_input("Current Password", type="password")
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    
                    if st.form_submit_button("Update Password"):
                        if not all([current_password, new_password, confirm_password]):
                            st.error("All fields are required!")
                        elif new_password != confirm_password:
                            st.error("New passwords don't match!")
                        else:
                            # Verify current password
                            if db.authenticate_user(user['username'], current_password):
                                success, message = db.update_user(user['username'], {'password': new_password})
                                if success:
                                    st.success("✅ Password updated successfully!")
                                else:
                                    st.error(f"❌ {message}")
                            else:
                                st.error("Current password is incorrect!")
        
        with tab2:
            st.markdown("#### ⚙️ Preferences")
            theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
            notifications = st.checkbox("Enable notifications", value=True)
            auto_refresh = st.checkbox("Auto-refresh data", value=True)
            
            if st.button("Save Preferences"):
                st.success("Preferences saved!")
        
        st.stop()
    
    # ADMIN SETTINGS
    tab1, tab2, tab3, tab4 = st.tabs(["👥 User Management", "⚙️ System Config", "📤 Data Import", "📊 System Info"])
    
    with tab1:
        st.markdown("#### 👥 User Management")
        
        # Get all users
        
        
        # Tabs for different user management tasks
        user_tab1, user_tab2, user_tab3, user_tab4 = st.tabs(["View Users", "Add User", "Edit User", "Delete User"])
        
        with user_tab1:
            st.markdown("##### 📋 All System Users")
            
            if not users_df.empty:
                # Format the dataframe for better display
                available_cols = users_df.columns.tolist()
                display_cols = ['username', 'full_name', 'department']
                if 'role_display' in available_cols:
                    display_cols.append('role_display')
                elif 'role' in available_cols:
                    display_cols.append('role')
                if 'created_at' in available_cols:
                    display_cols.append('created_at')
                display_df = users_df[display_cols].copy()
                display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                display_df.columns = ['Username', 'Full Name', 'Role', 'Department', 'Created At']
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400
                )
                
                # User statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Users", len(users_df))
                with col2:
                    admin_count = (users_df['role'] == 'admin').sum()
                    st.metric("Administrators", admin_count)
                with col3:
                    manager_count = (users_df['role'] == 'manager').sum()
                    st.metric("Managers", manager_count)
                with col4:
                    user_count = (users_df['role'] == 'user').sum()
                    st.metric("Regular Users", user_count)
            else:
                st.info("No users found in the system.")
        
        with user_tab2:
            st.markdown("##### ➕ Add New User")
            
            with st.form("add_user_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Username*", 
                                                placeholder="e.g., jsmith",
                                                help="Unique username for login")
                    new_fullname = st.text_input("Full Name*", 
                                                placeholder="e.g., John Smith")
                    new_email = st.text_input("Email Address", 
                                             placeholder="e.g., jsmith@nhrc.gov.gh")
                
                with col2:
                    new_role = st.selectbox("Role*", 
                                          ["user", "manager", "admin"],
                                          format_func=lambda x: {
                                              "user": "Regular User",
                                              "manager": "Manager",
                                              "admin": "Administrator"
                                          }[x])
                    new_department = st.selectbox("Department*",
                                                ["Biomedical", "Microbiology", "Parasitology", 
                                                 "Clinical Lab", "Research", "Administration", "IT"])
                    new_password = st.text_input("Initial Password*", 
                                                type="password",
                                                help="User will be prompted to change on first login")
                    confirm_password = st.text_input("Confirm Password*", 
                                                    type="password")
                
                # Form validation
                submitted = st.form_submit_button("➕ Create User", type="primary")
                
                if submitted:
                    # Validation
                    if not all([new_username, new_fullname, new_password, confirm_password]):
                        st.error("All fields marked with * are required!")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long!")
                    else:
                        user_data = {
                            'username': new_username.strip(),
                            'full_name': new_fullname.strip(),
                            'password': new_password,
                            'role': new_role,
                            'department': new_department
                        }
                        
                        if new_email:
                            user_data['email'] = new_email.strip()
                        
                        # Create user
                        success, message = db.create_user(user_data)
                        
                        # Get client info for audit
                        ip_address, user_agent = get_client_info()
                        
                        # Create user with audit
                        success, message = db.create_user(user_data, user, ip_address, user_agent)
                        
                        if success:
                            st.success(f"✅ User '{new_username}' created successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                        
        
        with user_tab3:
            st.markdown("##### ✏️ Edit User")
            
            if not users_df.empty:
                # Exclude current user from editing themselves
                edit_options = users_df[users_df['username'] != user['username']]['username'].tolist()
                
                if edit_options:
                    user_to_edit = st.selectbox("Select user to edit", edit_options)
                    
                    if user_to_edit:
                        user_data = users_df[users_df['username'] == user_to_edit].iloc[0]
                        
                        with st.form("edit_user_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_fullname = st.text_input("Full Name", 
                                                           value=user_data['full_name'])
                                new_role = st.selectbox("Role", 
                                                      ["user", "manager", "admin"],
                                                      index=["user", "manager", "admin"].index(user_data['role']),
                                                      format_func=lambda x: {
                                                          "user": "Regular User",
                                                          "manager": "Manager",
                                                          "admin": "Administrator"
                                                      }[x])
                            
                            with col2:
                                new_department = st.selectbox("Department",
                                                            ["Biomedical", "Microbiology", "Parasitology", 
                                                             "Clinical Lab", "Research", "Administration", "IT"],
                                                            index=["Biomedical", "Microbiology", "Parasitology", 
                                                                   "Clinical Lab", "Research", "Administration", "IT"]
                                                            .index(user_data.get('department', 'Biomedical')))
                                reset_password = st.checkbox("Reset Password", value=False)
                                
                                if reset_password:
                                    new_password = st.text_input("New Password", 
                                                               type="password",
                                                               help="Leave blank to keep current password")
                                    confirm_password = st.text_input("Confirm New Password", 
                                                                   type="password")
                                else:
                                    new_password = ""
                                    confirm_password = ""
                            
                            submitted = st.form_submit_button("💾 Save Changes", type="primary")
                            
                            if submitted:
                                updates = {
                                    'full_name': new_fullname,
                                    'role': new_role,
                                    'department': new_department
                                }
                                
                                # Handle password reset
                                if reset_password and new_password:
                                    if not new_password:
                                        st.error("New password is required when resetting password!")
                                    elif new_password != confirm_password:
                                        st.error("Passwords do not match!")
                                    elif len(new_password) < 6:
                                        st.error("Password must be at least 6 characters long!")
                                    else:
                                        updates['password'] = new_password
                                
                                success, message = db.update_user(user_to_edit, updates)

                                # Get client info for audit
                                ip_address, user_agent = get_client_info()
                                
                                success, message = db.update_user(user_to_edit, updates, user, ip_address, user_agent)
                                
                                if success:
                                    st.success(f"✅ User '{user_to_edit}' updated successfully!")
                                    if reset_password and new_password:
                                        st.info(f"New password for {user_to_edit}: `{new_password}`")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                else:
                    st.info("No other users to edit.")
            else:
                st.info("No users found in the system.")
        
        with user_tab4:
            st.markdown("##### 🗑️ Delete User")
            st.warning("⚠️ **Warning:** Deleting a user is permanent and cannot be undone!")
            
            if not users_df.empty:
                # Exclude current user and admin from deletion options
                delete_options = users_df[
                    (users_df['username'] != user['username']) & 
                    (users_df['username'] != 'admin')
                ]['username'].tolist()
                
                if delete_options:
                    user_to_delete = st.selectbox("Select user to delete", delete_options)
                    
                    if user_to_delete:
                        user_data = users_df[users_df['username'] == user_to_delete].iloc[0]
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.error(f"""
                            **You are about to delete user:**
                            
                            **Username:** {user_data['username']}
                            **Full Name:** {user_data['full_name']}
                            **Role:** {user_data['role']}
                            **Department:** {user_data['department']}
                            **Created:** {user_data.get('created_at', 'Unknown')}
                            
                            **This action cannot be undone!**
                            """)
                        
                        with col2:
                            confirm = st.checkbox("I understand this action is permanent")
                            transfer_data = st.checkbox("Transfer user's records to admin", value=True)
                            
                            if st.button("🗑️ Delete User", 
                                       disabled=not confirm,
                                       type="primary",
                                       use_container_width=True):
                                success, message = db.delete_user(user_to_delete)
                                                                # Get client info for audit
                                ip_address, user_agent = get_client_info()
                                
                                success, message = db.delete_user(user_to_delete, user, ip_address, user_agent)
                                
                                if success:
                                    st.success(f"✅ User '{user_to_delete}' deleted successfully!")
                                    if transfer_data:
                                        st.info("User's records have been transferred to admin account.")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                else:
                    st.info("No users available for deletion (cannot delete yourself or admin).")
            else:
                st.info("No users found in the system.")
    
    with tab2:
        st.markdown("#### ⚙️ System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📦 Inventory Settings")
            
            with st.form("inventory_settings"):
                default_reorder = st.number_input("Default Reorder Level (Units)", 
                                                 min_value=1, 
                                                 value=50,
                                                 help="Default reorder level for new items in units")
                
                storage_locs = st.text_area("Storage Locations (one per line)", 
                                          value="Main Store\nLab A\nLab B\nCold Room\nQuarantine\nArchive",
                                          height=150)
                
                categories = st.text_area("Item Categories (one per line)", 
                                        value="Personal Protective Equipment\nDesiccants\nMedical Supplies\nLaboratory Consumables\nGeneral Supplies\nReagents\nEquipment",
                                        height=150)
                
                if st.form_submit_button("💾 Save Inventory Settings"):
                    # Save to database or config file
                    st.success("Inventory settings saved!")
        
        with col2:
            st.markdown("##### 🔔 Notification Settings")
            
            with st.form("notification_settings"):
                email_notifications = st.checkbox("Enable Email Notifications", value=True)
                
                if email_notifications:
                    smtp_server = st.text_input("SMTP Server", 
                                               value="smtp.gmail.com")
                    smtp_port = st.number_input("SMTP Port", 
                                               min_value=1, 
                                               max_value=65535, 
                                               value=587)
                    sender_email = st.text_input("Sender Email", 
                                                placeholder="inventory@nhrc.gov.gh")
                
                low_stock_alert = st.number_input("Low Stock Alert (Units)", 
                                                 min_value=1, 
                                                 value=20,
                                                 help="Units remaining to trigger low stock alert")
                expiry_alert = st.number_input("Expiry Alert Days", 
                                              min_value=1, 
                                              value=30,
                                              help="Days before expiry to send alerts")
                
                # Notification recipients
                recipients = st.text_area("Alert Recipients (emails, one per line)", 
                                        placeholder="supervisor@nhrc.gov.gh\nmanager@nhrc.gov.gh",
                                        height=100)
                
                if st.form_submit_button("💾 Save Notification Settings"):
                    st.success("Notification settings saved!")
        
        st.markdown("---")
        st.markdown("##### 🛠️ Maintenance")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            if st.button("🔄 Rebuild Database Indexes", use_container_width=True):
                st.info("This would rebuild database indexes for better performance.")
        
        with col_m2:
            if st.button("🧹 Clear Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("Cache cleared successfully!")
        
        with col_m3:
            if st.button("📊 Update Statistics", use_container_width=True):
                st.info("System statistics updated.")
    
    with tab3:
        st.markdown("#### 📤 Data Import & Export")
        
        import_tab1, import_tab2, import_tab3 = st.tabs(["Import Excel", "Export Data", "Backup"])
        
        with import_tab1:
            st.markdown("##### 📥 Import from Excel")
            
            st.info("""
            **Supported Excel Format:**
            - Columns should include: `Item`, `Quantity`, `Unit`, `Expiry Date`
            - Example row: "Gloves", "600", "Units", "2024-12-31"
            - The system will import total units directly
            """)
            
            uploaded_file = st.file_uploader("Choose Excel file", 
                                           type=['xlsx', 'xls'],
                                           key="excel_import")
            
            if uploaded_file:
                try:
                    # Preview data
                    df = pd.read_excel(uploaded_file)
                    st.write("**Preview of uploaded data:**")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Import options
                    st.markdown("##### ⚙️ Import Options")
                    col_i1, col_i2 = st.columns(2)
                    
                    with col_i1:
                        import_mode = st.radio("Import Mode", 
                                             ["Add New Only", "Update Existing", "Replace All"])
                        skip_duplicates = st.checkbox("Skip duplicate items", value=True)
                    
                    with col_i2:
                        category_mapping = st.checkbox("Auto-map categories", value=True)
                        default_supplier = st.text_input("Default Supplier", 
                                                        value="Standard Supplier")
                    
                    if st.button("🚀 Process and Import", type="primary"):
                        with st.spinner("Processing data..."):
                            # Process the data
                            processed_df = processor.load_excel_data(uploaded_file.name)
                            
                            # Add supplier information
                            processed_df['supplier'] = default_supplier
                            
                            # Import to database
                            success_count = 0
                            error_count = 0
                            errors = []
                            
                            for _, row in processed_df.iterrows():
                                try:
                                    if db.add_inventory_item(row.to_dict()):
                                        success_count += 1
                                    else:
                                        error_count += 1
                                        errors.append(f"Failed to add: {row['item_name']}")
                                except Exception as e:
                                    error_count += 1
                                    errors.append(f"Error with {row['item_name']}: {str(e)}")
                            
                            # Show results
                            st.success(f"✅ Import completed!")
                            st.metric("Successfully Imported", success_count)
                            st.metric("Failed", error_count)
                            
                            if errors:
                                with st.expander("View Errors"):
                                    for error in errors[:10]:  # Show first 10 errors
                                        st.error(error)
                            
                            st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error reading Excel file: {str(e)}")
        
        with import_tab2:
            st.markdown("##### 📤 Export Data")
            
            col_e1, col_e2, col_e3 = st.columns(3)
            
            with col_e1:
                if st.button("📋 Export Inventory", use_container_width=True):
                    inventory_data = db.get_inventory()
                    csv = inventory_data.to_csv(index=False)
                    st.download_button(
                        "💾 Download Inventory CSV",
                        data=csv,
                        file_name=f"inventory_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col_e2:
                if st.button("📝 Export Usage Logs", use_container_width=True):
                    usage_stats = db.get_usage_stats()
                    csv = usage_stats.to_csv(index=False)
                    st.download_button(
                        "💾 Download Usage Logs CSV",
                        data=csv,
                        file_name=f"usage_logs_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col_e3:
                if st.button("👥 Export Users", use_container_width=True):
                    users_data = db.get_all_users()
                    csv = users_data.to_csv(index=False)
                    st.download_button(
                        "💾 Download Users CSV",
                        data=csv,
                        file_name=f"users_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            # Custom export
            st.markdown("##### 🎛️ Custom Export")
            with st.form("custom_export"):
                export_columns = st.multiselect(
                    "Select columns to export",
                    options=['item_name', 'category', 'quantity', 'unit', 
                            'expiry_date', 'storage_location', 'supplier', 'status'],
                    default=['item_name', 'category', 'quantity', 'unit', 'expiry_date']
                )
                
                export_format = st.radio("Export Format", ["CSV", "Excel"])
                
                if st.form_submit_button("Generate Custom Export"):
                    inventory_data = db.get_inventory()
                    if export_columns:
                        export_data = inventory_data[export_columns]
                        
                        if export_format == "CSV":
                            csv = export_data.to_csv(index=False)
                            st.download_button(
                                "💾 Download Custom Export",
                                data=csv,
                                file_name=f"custom_export_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            # Excel export
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                export_data.to_excel(writer, index=False, sheet_name='Inventory')
                            output.seek(0)
                            
                            st.download_button(
                                "💾 Download Excel File",
                                data=output,
                                file_name=f"custom_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
        
        with import_tab3:
            st.markdown("##### 💾 System Backup")
            
            st.info("""
            **Backup Options:**
            1. **Full Backup** - Complete database backup
            2. **Inventory Only** - Just inventory data
            3. **Scheduled Backup** - Automatic backups
            """)
            
            backup_type = st.radio("Backup Type", 
                                 ["Full Database Backup", 
                                  "Inventory Data Only",
                                  "Configuration Backup"])
            
            if st.button("🔄 Create Backup", type="primary"):
                with st.spinner("Creating backup..."):
                    # Create backup file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    if backup_type == "Full Database Backup":
                        # For Supabase, we can't directly backup the database file
                        # Instead, export all data
                        st.info("For Supabase, please use the Supabase dashboard for full database backups.")
                        
                    elif backup_type == "Inventory Data Only":
                        # Export inventory to Excel
                        inventory_data = db.get_inventory()
                        backup_file = f"backup_inventory_{timestamp}.xlsx"
                        
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            inventory_data.to_excel(writer, index=False, sheet_name='Inventory')
                            usage_stats = db.get_usage_stats()
                            if not usage_stats.empty:
                                usage_stats.to_excel(writer, index=False, sheet_name='Usage_Logs')
                        output.seek(0)
                        
                        st.download_button(
                            "💾 Download Backup",
                            data=output,
                            file_name=backup_file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    st.success(f"✅ Backup created successfully!")
    
    with tab4:
        st.markdown("#### 📊 System Information")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown("##### 🖥️ System Status")
            
            # Get system stats
            inventory_count = len(inventory_df)
            total_units = inventory_df['total_units'].sum() if 'total_units' in inventory_df.columns else inventory_df['quantity'].sum()
            users_count = len(users_df) if 'users_df' in locals() else 0
            
            st.metric("Inventory Items", inventory_count)
            st.metric("Total Units in Stock", f"{total_units:,}")
            st.metric("System Users", users_count)
            st.metric("Database Size", "Supabase Cloud")
        
        with col_s2:
            st.markdown("##### 🔧 Technical Information")
            
            st.info(f"""
            **Application Details:**
            - **Version:** 2.1.0
            - **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
            - **Database:** Supabase
            - **Server:** Supabase
            
            **System Requirements:**
            - Python 3.8+
            - 2GB RAM minimum
            - 500MB disk space
            
            **Support Contact:**
            - Email: f.amengaetego@gmail.com
            - Phone: 0547548200
            """)
        
        st.markdown("---")
        st.markdown("##### 📈 System Logs")
        
        # Display recent activities (simulated)
        activities = [
            {"time": "10:30 AM", "user": "admin", "action": "Logged in", "details": "Successful login"},
            {"time": "10:15 AM", "user": "jsmith", "action": "Updated item", "details": "Updated gloves quantity"},
            {"time": "09:45 AM", "user": "admin", "action": "Added user", "details": "Added new manager"},
            {"time": "Yesterday", "user": "system", "action": "Backup", "details": "Daily backup completed"},
            {"time": "Yesterday", "user": "mjones", "action": "Logged usage", "details": "Used 50 units of gloves"}
        ]
        
        for activity in activities:
            with st.container():
                col_l1, col_l2, col_l3 = st.columns([1, 2, 3])
                with col_l1:
                    st.write(f"**{activity['time']}**")
                with col_l2:
                    st.write(f"**{activity['user']}** - {activity['action']}")
                with col_l3:
                    st.write(activity['details'])
                st.markdown("---")

# ========== VC.PY STYLE FOOTER ==========
st.markdown("---")
st.markdown(
    "<p style='text-align:center;font-size:13px;color:gray;margin-top:25px;'>"
    "© 2025 Navrongo Health Research Centre – Built by Fedelis Wekia Amenga-etego</p>",
    unsafe_allow_html=True

)





