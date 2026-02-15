import streamlit as st
import pandas as pd
from datetime import datetime
from db.db_manager import fetch_dsm_data
from data.mapping_loader import enrich_dsm_data


# Simple in-memory remarks storage (you can replace with DuckDB table later)
if 'remarks_data' not in st.session_state:
    st.session_state.remarks_data = []


def render_remarks():
    """Remarks Management System"""
    
    st.markdown("## 📝 Remarks & Action Items")
    
    # Load site data for dropdowns
    df = fetch_dsm_data()
    
    if df.empty:
        st.warning("⚠️ No data available. Upload data first.")
        return
    
    df = enrich_dsm_data(df)
    
    # ----------------------------
    # ADD NEW REMARK
    # ----------------------------
    with st.expander("➕ Add New Remark", expanded=False):
        with st.form("add_remark_form"):
            st.markdown("### Create New Remark")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                site_options = sorted(df["Site"].dropna().astype(str).unique().tolist())
                remark_site = st.selectbox("Site", site_options, key="new_site")
            
            with col2:
                remark_category = st.selectbox(
                    "Category",
                    ["Performance Issue", "Maintenance Required", "Data Anomaly", 
                     "Follow-up Needed", "Resolved", "Other"],
                    key="new_category"
                )
            
            with col3:
                remark_priority = st.selectbox(
                    "Priority",
                    ["🔴 High", "🟡 Medium", "🟢 Low"],
                    key="new_priority"
                )
            
            remark_title = st.text_input("Title", placeholder="Brief description...", key="new_title")
            remark_details = st.text_area("Details", placeholder="Detailed notes...", key="new_details")
            
            col_status, col_due = st.columns(2)
            
            with col_status:
                remark_status = st.selectbox(
                    "Status",
                    ["Open", "In Progress", "On Hold", "Resolved", "Closed"],
                    key="new_status"
                )
            
            with col_due:
                remark_due = st.date_input("Due Date", key="new_due")
            
            submitted = st.form_submit_button("💾 Save Remark", use_container_width=True)
            
            if submitted:
                if not remark_title:
                    st.error("Please enter a title")
                else:
                    new_remark = {
                        "id": len(st.session_state.remarks_data) + 1,
                        "site": remark_site,
                        "category": remark_category,
                        "priority": remark_priority,
                        "title": remark_title,
                        "details": remark_details,
                        "status": remark_status,
                        "due_date": remark_due.strftime("%Y-%m-%d"),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "created_by": "User"  # You can add authentication later
                    }
                    
                    st.session_state.remarks_data.append(new_remark)
                    st.success("✅ Remark saved successfully!")
                    st.rerun()
    
    st.markdown("---")
    
    # ----------------------------
    # FILTER REMARKS
    # ----------------------------
    st.markdown("### 🔍 Filter Remarks")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        site_options_all = ["All"] + sorted(df["Site"].dropna().astype(str).unique().tolist())
        filter_site = st.selectbox("Filter by Site", site_options_all, key="filter_site")
    
    with col2:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Open", "In Progress", "On Hold", "Resolved", "Closed"],
            key="filter_status"
        )
    
    with col3:
        filter_priority = st.selectbox(
            "Filter by Priority",
            ["All", "🔴 High", "🟡 Medium", "🟢 Low"],
            key="filter_priority"
        )
    
    with col4:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All", "Performance Issue", "Maintenance Required", "Data Anomaly", 
             "Follow-up Needed", "Resolved", "Other"],
            key="filter_category"
        )
    
    st.markdown("---")
    
    # ----------------------------
    # DISPLAY REMARKS
    # ----------------------------
    if not st.session_state.remarks_data:
        st.info("📝 No remarks yet. Add your first remark above!")
    else:
        # Apply filters
        filtered_remarks = st.session_state.remarks_data.copy()
        
        if filter_site != "All":
            filtered_remarks = [r for r in filtered_remarks if r["site"] == filter_site]
        
        if filter_status != "All":
            filtered_remarks = [r for r in filtered_remarks if r["status"] == filter_status]
        
        if filter_priority != "All":
            filtered_remarks = [r for r in filtered_remarks if r["priority"] == filter_priority]
        
        if filter_category != "All":
            filtered_remarks = [r for r in filtered_remarks if r["category"] == filter_category]
        
        st.markdown(f"### 📋 Remarks ({len(filtered_remarks)} items)")
        
        # Summary stats
        if filtered_remarks:
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            open_count = len([r for r in filtered_remarks if r["status"] == "Open"])
            in_progress_count = len([r for r in filtered_remarks if r["status"] == "In Progress"])
            high_priority = len([r for r in filtered_remarks if r["priority"] == "🔴 High"])
            resolved_count = len([r for r in filtered_remarks if r["status"] == "Resolved"])
            
            stat_col1.metric("Open", open_count)
            stat_col2.metric("In Progress", in_progress_count)
            stat_col3.metric("High Priority", high_priority)
            stat_col4.metric("Resolved", resolved_count)
            
            st.markdown("---")
        
        # Display each remark as card
        for remark in filtered_remarks:
            with st.container():
                # Header
                col_title, col_actions = st.columns([5, 1])
                
                with col_title:
                    st.markdown(f"### {remark['priority']} {remark['title']}")
                    st.caption(f"**Site:** {remark['site']} | **Category:** {remark['category']} | **Created:** {remark['created_at']}")
                
                with col_actions:
                    if st.button("🗑️", key=f"delete_{remark['id']}"):
                        st.session_state.remarks_data = [
                            r for r in st.session_state.remarks_data if r['id'] != remark['id']
                        ]
                        st.rerun()
                
                # Details
                col_details, col_meta = st.columns([3, 1])
                
                with col_details:
                    st.write(remark['details'])
                
                with col_meta:
                    # Status selector (editable)
                    new_status = st.selectbox(
                        "Status",
                        ["Open", "In Progress", "On Hold", "Resolved", "Closed"],
                        index=["Open", "In Progress", "On Hold", "Resolved", "Closed"].index(remark['status']),
                        key=f"status_{remark['id']}"
                    )
                    
                    if new_status != remark['status']:
                        # Update status
                        for r in st.session_state.remarks_data:
                            if r['id'] == remark['id']:
                                r['status'] = new_status
                        st.rerun()
                    
                    st.write(f"**Due:** {remark['due_date']}")
                    st.write(f"**By:** {remark['created_by']}")
                
                st.markdown("---")
    
    # ----------------------------
    # EXPORT REMARKS
    # ----------------------------
    if st.session_state.remarks_data:
        st.markdown("### 📤 Export Remarks")
        
        # Convert to DataFrame
        remarks_df = pd.DataFrame(st.session_state.remarks_data)
        
        # Download button
        csv = remarks_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv,
            file_name=f"dsm_remarks_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Show data table
        with st.expander("📊 View as Table"):
            st.dataframe(remarks_df, use_container_width=True, hide_index=True)
