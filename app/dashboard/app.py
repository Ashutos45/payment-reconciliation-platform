import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import time

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
HEALTH_URL = "http://127.0.0.1:8000/health"

# Page Configuration
st.set_page_config(
    page_title="FinRecon Pro",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern card-style layout and clean UI
st.markdown("""
<style>
    .kpi-card {
        background-color: #1a1a1a;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        border: 1px solid #2d2d2d;
        margin-bottom: 24px;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        border-color: #4CAF50;
    }
    .kpi-title {
        color: #a0a0a0;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    .kpi-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 700;
    }
    .status-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
        display: inline-block;
    }
    .status-healthy { background-color: rgba(40, 167, 69, 0.2); color: #4CAF50; border: 1px solid #4CAF50; }
    .status-error { background-color: rgba(220, 53, 69, 0.2); color: #ff5252; border: 1px solid #ff5252; }
    .status-warning { background-color: rgba(255, 193, 7, 0.2); color: #ffc107; border: 1px solid #ffc107; }
    
    /* Clean up default Streamlit elements */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# API HELPER FUNCTIONS
# ==============================================================================
@st.cache_data(ttl=5)
def check_health() -> bool:
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def api_call(method: str, endpoint: str, **kwargs) -> Optional[Any]:
    """Generic API caller with error handling."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        
        if response.headers.get('content-type') == 'application/json':
            return response.json()
        return response.content
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get('detail', str(e)) if e.response else str(e)
        st.error(f"API Error: {detail}")
        return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

# ==============================================================================
# UI COMPONENTS
# ==============================================================================
def render_kpi_card(title: str, value: str, prefix: str = ""):
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{prefix}{value}</div>
        </div>
    """, unsafe_allow_html=True)

def render_badge(text: str, level: str = "healthy"):
    st.markdown(f'<span class="status-badge status-{level}">{text}</span>', unsafe_allow_html=True)

# ==============================================================================
# PAGE SECTIONS
# ==============================================================================

def page_dashboard():
    st.title("📊 Executive Dashboard")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()
            
    metrics = api_call("GET", "/metrics")
    
    if not metrics or metrics.get('total_internal', 0) == 0:
        st.warning("No reconciliation data available. Please upload files and run the engine.")
        return

    # KPI Row 1
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi_card("Total Transactions", f"{metrics['total_internal']:,}")
    with c2: render_kpi_card("Match Rate", f"{metrics['match_rate']}%")
    with c3: render_kpi_card("Total Exceptions", f"{metrics.get('total_exceptions', 0):,}")
    with c4: render_kpi_card("Unmatched Volume", f"{metrics['unmatched_amount']:,.2f}", "$")

    st.markdown("---")
    
    # Charts Row
    c1, c2 = st.columns(2)
    with c1:
        unmatched = metrics['total_internal'] - metrics['total_matched']
        fig = go.Figure(data=[go.Pie(
            labels=['Exact', 'Fuzzy', 'Unmatched'], 
            values=[metrics['exact_matches'], metrics['fuzzy_matches'], unmatched],
            hole=.5,
            marker_colors=['#4CAF50', '#FFC107', '#ff5252']
        )])
        fig.update_layout(title="Reconciliation Distribution", paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        exc = metrics.get('exceptions_by_type', {})
        if exc:
            df = pd.DataFrame(list(exc.items()), columns=['Type', 'Count'])
            fig = px.bar(df, x='Type', y='Count', title="Exceptions Breakdown", color='Type')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No exceptions detected! Great job.")

def page_upload_reconcile():
    st.title("⚙️ Engine Operations")
    
    st.subheader("1. Ingest Data")
    c1, c2 = st.columns(2)
    with c1: int_file = st.file_uploader("Internal Ledger", type=['csv', 'xlsx', 'xls'])
    with c2: bnk_file = st.file_uploader("Bank Statement", type=['csv', 'xlsx', 'xls'])
    
    if st.button("Upload & Parse Files", type="primary"):
        if int_file and bnk_file:
            with st.spinner("Parsing and validating files..."):
                files = {
                    'internal_file': (int_file.name, int_file, 'application/octet-stream'),
                    'bank_file': (bnk_file.name, bnk_file, 'application/octet-stream')
                }
                res = api_call("POST", "/upload", files=files)
                if res:
                    st.success(f"Successfully loaded {res['internal_records']} internal and {res['bank_records']} bank records.")
        else:
            st.warning("Please upload both files.")
            
    st.markdown("---")
    st.subheader("2. Run Reconciliation")
    if st.button("🚀 Execute Matching Algorithms"):
        with st.spinner("Running exact and fuzzy heuristics..."):
            res = api_call("POST", "/reconcile")
            if res:
                st.success("Reconciliation completed!")
                time.sleep(1)
                st.session_state.current_page = "📊 Dashboard"
                st.rerun()

def page_search():
    st.title("🔍 Global Transaction Search")
    
    tx_id = st.text_input("Enter Transaction ID to trace through the entire platform:")
    
    if st.button("Search", type="primary") and tx_id:
        with st.spinner("Searching database..."):
            res = api_call("GET", f"/transactions/{tx_id}")
            if res:
                st.success("Transaction Found!")
                
                # Core Info
                st.subheader("Ledger Records")
                st.dataframe(pd.DataFrame(res['records']), use_container_width=True)
                
                # Recon Status
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Reconciliation Status")
                    if res.get('reconciliation'):
                        r = res['reconciliation']
                        st.json(r)
                    else:
                        st.warning("Unmatched / Not processed")
                        
                with c2:
                    st.subheader("Detected Exceptions")
                    if res.get('exceptions'):
                        st.error(f"Found {len(res['exceptions'])} exceptions!")
                        for exc in res['exceptions']:
                            st.markdown(f"**{exc['severity']}**: {exc['type']}")
                            st.write(exc['details'])
                            st.info(f"💡 {exc['recommendation']}")
                    else:
                        st.success("No exceptions linked to this transaction.")

def page_exceptions():
    st.title("⚠️ Exception Command Center")
    
    exc = api_call("GET", "/exceptions?limit=1000")
    if not exc:
        st.info("No exceptions found.")
        return
        
    df = pd.DataFrame(exc)
    
    # Filters
    c1, c2 = st.columns(2)
    with c1:
        sev_filter = st.multiselect("Filter by Severity", options=["HIGH", "MEDIUM", "LOW"])
    with c2:
        type_filter = st.multiselect("Filter by Type", options=df['exception_type'].unique())
        
    if sev_filter: df = df[df['severity'].isin(sev_filter)]
    if type_filter: df = df[df['exception_type'].isin(type_filter)]
    
    st.dataframe(df, use_container_width=True, hide_index=True)

def page_export():
    st.title("💾 Export & Compliance")
    st.markdown("Generate secure, multi-sheet Excel reports containing full reconciliation trails.")
    
    if st.button("Generate Complete Report", type="primary"):
        with st.spinner("Compiling sheets and formatting data..."):
            content = api_call("GET", "/export")
            if content:
                st.success("Ready for download!")
                st.download_button(
                    label="⬇️ Download .xlsx",
                    data=content,
                    file_name=f"Recon_Report_{int(time.time())}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

# ==============================================================================
# MAIN ROUTER
# ==============================================================================
def main():
    st.sidebar.title("🏦 FinRecon Pro")
    
    if check_health():
        st.sidebar.markdown('<span class="status-badge status-healthy">🟢 System Online</span>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<span class="status-badge status-error">🔴 System Offline</span>', unsafe_allow_html=True)
        
    st.sidebar.markdown("---")
    
    pages = {
        "📊 Dashboard": page_dashboard,
        "⚙️ Engine Ops": page_upload_reconcile,
        "🔍 Search": page_search,
        "⚠️ Exceptions": page_exceptions,
        "💾 Export": page_export
    }
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "📊 Dashboard"
        
    selected = st.sidebar.radio("Navigation", list(pages.keys()), index=list(pages.keys()).index(st.session_state.current_page))
    st.session_state.current_page = selected
    
    pages[selected]()

if __name__ == "__main__":
    main()
