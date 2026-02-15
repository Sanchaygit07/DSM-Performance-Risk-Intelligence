import streamlit as st
import pandas as pd
from db.db_manager import (
    initialize_database,
    insert_dsm_data,
    detect_duplicates,
    preview_schema_mapping,
    get_ingestion_logs,
)
from db.init_db import init_database

# Auto create DB on startup
init_database()
from utils.column_mapper import standardize_columns, get_mapping_report

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="DSM Intelligence Platform",
    layout="wide",
    initial_sidebar_state="collapsed",  # Hide sidebar, use top navigation
)

initialize_database()

# ===============================
# SESSION STATE FOR THEME
# ===============================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ===============================
# CUSTOM CSS FOR NAVIGATION
# ===============================
# Theme colors
if st.session_state.theme == "dark":
    bg_color = "#0e1117"
    text_color = "#ffffff"
    border_color = "#2c2f36"
else:
    bg_color = "#ffffff"
    text_color = "#000000"
    border_color = "#e0e0e0"

st.markdown(f"""
<style>
    /* Hide default sidebar */
    [data-testid="stSidebar"] {{
        display: none;
    }}
    
    /* Remove default header padding */
    .main .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }}
    
    /* Reduce spacing between elements */
    .element-container {{
        margin-bottom: 0.5rem !important;
    }}
    
    div[data-testid="stVerticalBlock"] > div {{
        gap: 0.5rem !important;
    }}
    
    /* Compact expanders */
    .streamlit-expanderHeader {{
        padding: 0.5rem !important;
    }}
</style>
""", unsafe_allow_html=True)

# ===============================
# SESSION DEFAULTS
# ===============================
if "threshold" not in st.session_state:
    st.session_state.threshold = 5.0

if "forecast_horizon" not in st.session_state:
    st.session_state.forecast_horizon = 3

if "upload_stage" not in st.session_state:
    st.session_state.upload_stage = "idle"

if "staged_data" not in st.session_state:
    st.session_state.staged_data = None

if "staged_filename" not in st.session_state:
    st.session_state.staged_filename = None

if "duplicate_info" not in st.session_state:
    st.session_state.duplicate_info = None

if "show_diagnostics" not in st.session_state:
    st.session_state.show_diagnostics = False

if "current_page" not in st.session_state:
    st.session_state.current_page = "Executive"

if "selected_state" not in st.session_state:
    st.session_state.selected_state = None

# ===============================
# COMPACT TOP NAVIGATION WITH THEME TOGGLE
# ===============================
header_col1, header_col2, header_col3 = st.columns([2, 6, 1])

with header_col1:
    st.markdown(f"### 🚀 DSM Intelligence")

with header_col2:
    # Navigation tabs with active highlighting
    tab_col1, tab_col2, tab_col3, tab_col4 = st.columns(4)
    
    with tab_col1:
        exec_color = "primary" if st.session_state.current_page == "Executive" else "secondary"
        if st.button("Executive", key="nav_executive", type=exec_color, use_container_width=True):
            st.session_state.current_page = "Executive"
            st.rerun()
    
    with tab_col2:
        port_color = "primary" if st.session_state.current_page == "Portfolio" else "secondary"
        if st.button("Portfolio", key="nav_portfolio", type=port_color, use_container_width=True):
            st.session_state.current_page = "Portfolio"
            st.rerun()
    
    with tab_col3:
        drill_color = "primary" if st.session_state.current_page == "Site Drilldown" else "secondary"
        if st.button("Site Drilldown", key="nav_drilldown", type=drill_color, use_container_width=True):
            st.session_state.current_page = "Site Drilldown"
            st.rerun()
    
    with tab_col4:
        rem_color = "primary" if st.session_state.current_page == "Remarks" else "secondary"
        if st.button("Remarks", key="nav_remarks", type=rem_color, use_container_width=True):
            st.session_state.current_page = "Remarks"
            st.rerun()

with header_col3:
    # Theme toggle
    if st.button("🌓 Theme", key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

st.divider()

# ===============================
# FILE UPLOAD SECTION (Compact)
# ===============================
with st.expander("📤 Upload DSM Raw File", expanded=False):
    
    uploaded_file = st.file_uploader(
        "Upload CSV/XLSX", 
        type=["csv", "xlsx"],
        key="file_uploader"
    )
    
    show_diagnostics = st.checkbox("🔬 Show Ingestion Diagnostics", value=st.session_state.show_diagnostics)
    st.session_state.show_diagnostics = show_diagnostics
    
    if uploaded_file and st.session_state.upload_stage == "idle":
        try:
            with st.spinner("🔄 Processing file..."):
                # Load file
                if uploaded_file.name.endswith(".csv"):
                    df_raw = pd.read_csv(uploaded_file)
                else:
                    xl = pd.ExcelFile(uploaded_file)
                    if "raw Data" in xl.sheet_names:
                        df_raw = pd.read_excel(uploaded_file, sheet_name="raw Data")
                    else:
                        df_raw = pd.read_excel(uploaded_file)
                
                # Clean
                df_raw = df_raw.dropna(axis=1, how="all")
                df_raw.columns = df_raw.columns.str.strip()
                
                # Map columns
                df_mapped = standardize_columns(df_raw)
                mapping_report = get_mapping_report(df_raw)
                
                # Auto-clean nulls and duplicates
                if 'Site' in df_mapped.columns:
                    df_mapped = df_mapped.dropna(subset=['Site'], how='any')
                if 'Month' in df_mapped.columns:
                    df_mapped = df_mapped.dropna(subset=['Month'], how='any')
                
                # Remove internal duplicates
                if 'Site' in df_mapped.columns and 'Month' in df_mapped.columns:
                    before_dedup = len(df_mapped)
                    df_mapped = df_mapped.drop_duplicates(subset=['Site', 'Month'], keep='last')
                    after_dedup = len(df_mapped)
                    
                    if after_dedup < before_dedup:
                        st.warning(f"⚠️ Removed {before_dedup - after_dedup} duplicate rows")
            
            # Diagnostics
            if st.session_state.show_diagnostics:
                st.markdown("### 🔬 Mapping Diagnostics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.success(f"✅ Matched: {len(mapping_report['matched'])}")
                with col2:
                    st.warning(f"⚠️ Unmatched: {len(mapping_report['unmatched'])}")
                with col3:
                    st.error(f"❌ Missing: {len(mapping_report['missing'])}")
            
            # Detect duplicates
            existing_rows, new_rows = detect_duplicates(df_mapped)
            
            st.session_state.staged_data = df_mapped
            st.session_state.staged_filename = uploaded_file.name
            st.session_state.duplicate_info = {
                "existing_count": len(existing_rows),
                "new_count": len(new_rows),
            }
            
            if len(existing_rows) > 0:
                st.session_state.upload_stage = "pending_confirmation"
            else:
                st.session_state.upload_stage = "processing"
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
            st.session_state.upload_stage = "idle"
    
    # Duplicate confirmation UI
    if st.session_state.upload_stage == "pending_confirmation":
        dup_info = st.session_state.duplicate_info
        st.warning(f"⚠️ Found {dup_info['existing_count']} existing records")
        
        col1, col2 = st.columns(2)
        
        if col1.button("✅ Overwrite", type="primary"):
            stats = insert_dsm_data(
                st.session_state.staged_data,
                overwrite_duplicates=True,
                filename=st.session_state.staged_filename
            )
            st.success(f"✅ Inserted: {stats['inserted']}, Updated: {stats['updated']}")
            st.session_state.upload_stage = "idle"
            st.rerun()
        
        if col2.button("⏭️ Skip Duplicates"):
            stats = insert_dsm_data(
                st.session_state.staged_data,
                overwrite_duplicates=False,
                filename=st.session_state.staged_filename
            )
            st.info(f"✅ Inserted: {stats['inserted']}, Skipped: {stats['skipped']}")
            st.session_state.upload_stage = "idle"
            st.rerun()
    
    # Auto-insert
    if st.session_state.upload_stage == "processing":
        stats = insert_dsm_data(
            st.session_state.staged_data,
            overwrite_duplicates=True,
            filename=st.session_state.staged_filename
        )
        st.success(f"✅ Uploaded {stats['inserted']} rows")
        st.session_state.upload_stage = "idle"

# ===============================
# PAGE ROUTING
# ===============================
page = st.session_state.current_page

if page == "Executive":
    from views.executive_view import render_executive_view
    render_executive_view()

elif page == "Portfolio":
    from views.portfolio_analysis import render_portfolio_analysis
    render_portfolio_analysis()

elif page == "Site Drilldown":
    from views.site_drilldown import render_site_drilldown
    render_site_drilldown()

elif page == "Remarks":
    try:
        from views.remarks import render_remarks
        render_remarks()
    except ImportError:
        st.warning("Remarks feature coming soon!")
