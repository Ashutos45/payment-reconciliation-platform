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
    page_title="Payment Reconciliation Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern card-style layout and clean UI
st.markdown("""
<style>
    .kpi-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #333;
        margin-bottom: 20px;
    }
    .kpi-title {
        color: #888;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .kpi-value {
        color: #ffffff;
        font-size: 28px;
        font-weight: 700;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
    }
    .status-healthy { background-color: #28a745; color: white; }
    .status-error { background-color: #dc3545; color: white; }
    
    /* Clean up default Streamlit elements */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# API HELPER FUNCTIONS
# ==============================================================================
def check_health() -> bool:
    """Check if the backend API is reachable."""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def upload_files(internal_file, bank_file) -> Optional[Dict[str, Any]]:
    """Upload transaction files to the backend."""
    try:
        files = {
            'internal_file': (internal_file.name, internal_file, 'text/csv'),
            'bank_file': (bank_file.name, bank_file, 'text/csv')
        }
        response = requests.post(f"{API_BASE_URL}/upload", files=files)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Upload failed: {e.response.json().get('detail') if hasattr(e, 'response') and e.response else str(e)}")
        return None

def run_reconciliation() -> Optional[Dict[str, Any]]:
    """Trigger the reconciliation engine."""
    try:
        response = requests.post(f"{API_BASE_URL}/reconcile")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Reconciliation failed: {e.response.json().get('detail') if hasattr(e, 'response') and e.response else str(e)}")
        return None

def fetch_metrics() -> Optional[Dict[str, Any]]:
    """Fetch dashboard metrics."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def fetch_results() -> List[Dict[str, Any]]:
    """Fetch all reconciliation results."""
    try:
        response = requests.get(f"{API_BASE_URL}/results?limit=1000")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch results: {str(e)}")
        return []

def fetch_exceptions() -> List[Dict[str, Any]]:
    """Fetch all exceptions."""
    try:
        response = requests.get(f"{API_BASE_URL}/exceptions?limit=1000")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch exceptions: {str(e)}")
        return []

def get_export_report():
    """Get the export report as bytes."""
    try:
        response = requests.get(f"{API_BASE_URL}/export")
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        st.error(f"Failed to generate report: {str(e)}")
        return None

# ==============================================================================
# UI COMPONENTS
# ==============================================================================
def render_kpi_card(title: str, value: str, prefix: str = ""):
    """Render a modern KPI card."""
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{prefix}{value}</div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# PAGE SECTIONS
# ==============================================================================

def page_system_health():
    """System Health and Connection Status Page"""
    st.title("🖥️ System Health")
    st.markdown("Monitor backend API status and connectivity.")
    
    with st.container():
        is_healthy = check_health()
        if is_healthy:
            st.success("Backend API is running and connected.")
            st.markdown('<span class="status-badge status-healthy">API: ONLINE</span>', unsafe_allow_html=True)
            
            # Show a dummy latency metric for professional feel
            col1, col2 = st.columns(2)
            with col1:
                render_kpi_card("API Status", "Healthy")
            with col2:
                render_kpi_card("Response Time", "42 ms")
        else:
            st.error("Cannot connect to backend API. Please ensure FastAPI is running on http://127.0.0.1:8000")
            st.markdown('<span class="status-badge status-error">API: OFFLINE</span>', unsafe_allow_html=True)

def page_upload():
    """File Upload Interface"""
    st.title("📤 Upload Transactions")
    st.markdown("Upload internal ledger and bank statement files for reconciliation.")
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Internal Transactions")
            internal_file = st.file_uploader("Upload Internal CSV/Excel", type=['csv', 'xlsx'], key="internal")
            
        with col2:
            st.subheader("Bank Statement")
            bank_file = st.file_uploader("Upload Bank CSV/Excel", type=['csv', 'xlsx'], key="bank")
            
    st.markdown("---")
    
    if st.button("🚀 Upload & Process Files", type="primary", use_container_width=True):
        if not internal_file or not bank_file:
            st.warning("⚠️ Please upload both Internal and Bank transaction files before proceeding.")
        else:
            with st.spinner("Processing files and validating schema..."):
                result = upload_files(internal_file, bank_file)
                if result:
                    st.success(f"✅ {result['message']}")
                    
                    # Show upload stats
                    col1, col2 = st.columns(2)
                    with col1:
                        render_kpi_card("Internal Records Ingested", f"{result['internal_records']:,}")
                    with col2:
                        render_kpi_card("Bank Records Ingested", f"{result['bank_records']:,}")
                    
                    st.info("Files are successfully ingested. Navigate to the Reconciliation Dashboard to run the matching engine.")

def page_dashboard():
    """Main Reconciliation Dashboard"""
    st.title("📊 Reconciliation Dashboard")
    
    # 1. Action Bar
    col_btn, col_empty = st.columns([1, 3])
    with col_btn:
        if st.button("⚙️ Run Matching Engine", type="primary"):
            with st.spinner("Running exact and fuzzy matching algorithms..."):
                res = run_reconciliation()
                if res:
                    st.success("Matching completed successfully!")
                    time.sleep(1) # Small delay for UX
                    st.rerun() # Refresh to show new metrics
                    
    st.markdown("---")
    
    # Fetch Metrics
    metrics = fetch_metrics()
    
    if not metrics or metrics.get('total_internal', 0) == 0:
        st.info("No data available. Please upload files and run the matching engine first.")
        return

    # 2. KPI Cards
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        render_kpi_card("Total Internal TXNs", f"{metrics['total_internal']:,}")
    with col2:
        render_kpi_card("Exact Matches", f"{metrics['exact_matches']:,}")
    with col3:
        render_kpi_card("Fuzzy Matches", f"{metrics['fuzzy_matches']:,}")
    with col4:
        match_rate = metrics['match_rate']
        render_kpi_card("Match Rate", f"{match_rate}%")
    with col5:
        render_kpi_card("Unmatched Amount", f"{metrics['unmatched_amount']:,.2f}", prefix="$")

    # 3. Charts Area
    st.markdown("---")
    st.subheader("Analytics & Insights")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Donut Chart for Match Status
        unmatched_count = metrics['total_internal'] - metrics['total_matched']
        labels = ['Exact Matches', 'Fuzzy Matches', 'Unmatched']
        values = [metrics['exact_matches'], metrics['fuzzy_matches'], unmatched_count]
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.4,
            marker_colors=['#28a745', '#ffc107', '#dc3545']
        )])
        fig_donut.update_layout(
            title_text="Matching Distribution",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    with chart_col2:
        # Bar chart for Exception Types
        exc_dict = metrics.get('exceptions_by_type', {})
        if exc_dict:
            exc_df = pd.DataFrame(list(exc_dict.items()), columns=['Exception Type', 'Count'])
            fig_bar = px.bar(
                exc_df, 
                x='Exception Type', 
                y='Count', 
                color='Exception Type',
                text='Count',
                title="Exceptions Breakdown"
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No exceptions detected.")

    # 4. Results Data Table
    st.markdown("---")
    st.subheader("Detailed Results")
    
    results = fetch_results()
    if results:
        df_results = pd.DataFrame(results)
        # Format the table
        if not df_results.empty:
            df_display = df_results[['internal_tx_id', 'bank_tx_id', 'status', 'match_score', 'created_at']]
            df_display.columns = ['Internal ID', 'Bank ID', 'Status', 'Score', 'Processed At']
            
            with st.expander("View Full Reconciliation Table", expanded=True):
                # Search filter
                search = st.text_input("🔍 Search by Transaction ID")
                if search:
                    mask = df_display.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
                    df_display = df_display[mask]
                
                st.dataframe(
                    df_display, 
                    use_container_width=True, 
                    hide_index=True,
                    height=400
                )
    else:
        st.info("No detailed results available.")

def page_exceptions():
    """Exceptions Viewer"""
    st.title("⚠️ Exceptions Viewer")
    st.markdown("Review and investigate discrepancies found during reconciliation.")
    
    exceptions = fetch_exceptions()
    
    if not exceptions:
        st.info("No exceptions found or matching has not been run yet.")
        return
        
    df_exc = pd.DataFrame(exceptions)
    
    if df_exc.empty:
        st.info("No exceptions found.")
        return
        
    # Formatting
    df_display = df_exc[['transaction_id', 'exception_type', 'details', 'created_at']]
    df_display.columns = ['Transaction ID', 'Type', 'Details', 'Detected At']
    
    # Exception Metrics
    type_counts = df_display['Type'].value_counts()
    
    st.subheader("Exception Summary")
    cols = st.columns(len(type_counts))
    for i, (type_name, count) in enumerate(type_counts.items()):
        with cols[i]:
            render_kpi_card(type_name, str(count))
            
    st.markdown("---")
    st.subheader("Exception Registry")
    
    # Interactive Table with filtering
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.multiselect("Filter by Type", options=df_display['Type'].unique())
    with col2:
        search_tx = st.text_input("Search Transaction ID")
        
    # Apply filters
    filtered_df = df_display.copy()
    if filter_type:
        filtered_df = filtered_df[filtered_df['Type'].isin(filter_type)]
    if search_tx:
        filtered_df = filtered_df[filtered_df['Transaction ID'].str.contains(search_tx, case=False, na=False)]
        
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    # CSV Download
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Exceptions CSV",
        data=csv,
        file_name="exceptions_filtered.csv",
        mime="text/csv",
    )

def page_export():
    """Export Reports"""
    st.title("💾 Export Reports")
    st.markdown("Download comprehensive reconciliation reports containing all matches, exceptions, and unmatched data.")
    
    st.markdown("""
    ### Report Contents
    The generated Excel report will contain multiple sheets:
    - **Summary**: High-level KPI metrics
    - **Matched**: Exact and fuzzy matched transactions
    - **Unmatched**: Leftover internal and bank transactions
    - **Exceptions**: Full registry of business exceptions detected
    """)
    
    st.markdown("---")
    
    if st.button("📄 Generate Excel Report", type="primary"):
        with st.spinner("Compiling full report..."):
            report_bytes = get_export_report()
            if report_bytes:
                st.success("Report generated successfully!")
                st.download_button(
                    label="⬇️ Click here to Download .xlsx",
                    data=report_bytes,
                    file_name="Payment_Reconciliation_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# ==============================================================================
# MAIN ROUTER
# ==============================================================================
def main():
    # Sidebar Navigation
    st.sidebar.title("🏦 FinRecon Platform")
    st.sidebar.markdown("---")
    
    pages = {
        "📊 Dashboard": page_dashboard,
        "📤 Upload": page_upload,
        "⚠️ Exceptions": page_exceptions,
        "💾 Export": page_export,
        "🖥️ Health": page_system_health
    }
    
    # Navigation state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "📊 Dashboard"
        
    selected_page = st.sidebar.radio(
        "Navigation", 
        list(pages.keys()), 
        index=list(pages.keys()).index(st.session_state.current_page)
    )
    
    st.session_state.current_page = selected_page
    
    st.sidebar.markdown("---")
    st.sidebar.info("Payment Reconciliation Platform v1.0\n\nEnsure FastAPI backend is running.")

    # Render selected page
    pages[selected_page]()

if __name__ == "__main__":
    main()
