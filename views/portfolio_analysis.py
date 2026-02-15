import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import os
from db.db_manager import fetch_dsm_data
from data.mapping_loader import enrich_dsm_data, load_site_mapping
from utils.fy_generator import generate_financial_year


def render_portfolio_analysis():
    """Portfolio Analytics Dashboard with ALL 4 QCAs guaranteed"""
    
    st.markdown("## 📊 Portfolio Analytics Dashboard")
    
    df = fetch_dsm_data()
    
    if df.empty:
        st.warning("⚠️ No data available. Please upload a file.")
        return
    
    df = enrich_dsm_data(df)
    
    df["Date"] = pd.to_datetime(df["Month"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["FY"] = df["Date"].dt.year.apply(lambda y: f"FY{y}")
    
    # Ensure all metadata columns exist
    for col in ["State", "State_Code", "Power_Sale_Category", "QCA", "Technology"]:
        if col not in df.columns:
            df[col] = "Unknown"
        df[col] = df[col].fillna("Unknown")
    
    df["Generation_MU"] = df["Measured_Energy_kWh"] / 1_000_000
    df["Revenue_Cr"] = df["Actual_Revenue_INR"] / 10_000_000
    df["Penalty_Cr"] = df["Total_Penalty_INR"] / 10_000_000
    df["Penalty_L"] = df["Total_Penalty_INR"] / 100_000
    
    # FILTERS
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        fy_options = sorted(df["FY"].dropna().unique())
        fy = st.multiselect("FY", fy_options, key="port_fy")
    
    with col2:
        site_options = sorted(df["Site"].dropna().astype(str).unique().tolist())
        site = st.selectbox("Site", ["All"] + site_options, key="port_site")
    
    with col3:
        cat_options = [c for c in sorted(df["Power_Sale_Category"].unique()) if c != "Unknown"]
        category = st.selectbox("Category", ["All"] + cat_options, key="port_cat")
    
    with col4:
        qca_options = [q for q in sorted(df["QCA"].unique()) if q != "Unknown"]
        qca = st.selectbox("QCA", ["All"] + qca_options, key="port_qca")
    
    with col5:
        state_options = [s for s in sorted(df["State"].unique()) if s != "Unknown"]
        state = st.selectbox("State", ["All"] + state_options, key="port_state")
    
    with col6:
        threshold = st.number_input("Threshold %", value=5.0, step=0.5, key="port_thresh")
    
    filtered = df.copy()
    if fy:
        filtered = filtered[filtered["FY"].isin(fy)]
    if site != "All":
        filtered = filtered[filtered["Site"] == site]
    if category != "All":
        filtered = filtered[filtered["Power_Sale_Category"] == category]
    if qca != "All":
        filtered = filtered[filtered["QCA"] == qca]
    if state != "All":
        filtered = filtered[filtered["State"] == state]
    
    if filtered.empty:
        st.warning("⚠️ No data matches filters.")
        return
    
    st.divider()
    
    # CHART 1 & 2: PARETO + CATEGORY
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        st.markdown("### 📊 Penalty Contribution by Site (Pareto)")
        
        site_penalties = filtered.groupby("Site")["Penalty_L"].sum().sort_values(ascending=False).head(10)
        colors = ['#ef4444' if i < 3 else '#4da6ff' for i in range(len(site_penalties))]
        
        fig_pareto = go.Figure()
        fig_pareto.add_bar(
            x=site_penalties.index,
            y=site_penalties.values,
            marker_color=colors,
            text=[f"₹{v:.1f}L" for v in site_penalties.values],
            textposition='outside'
        )
        
        fig_pareto.update_layout(
            height=400,
            yaxis_title="Penalty (₹ Lakh)",
            xaxis_title="Site",
            template="plotly_dark",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_pareto, use_container_width=True)
    
    with row1_col2:
        st.markdown("### 📊 Category-wise Commercial Loss vs Generation")
        
        cat_data = filtered.groupby("Power_Sale_Category").agg({
            "Generation_MU": "sum",
            "Revenue_Cr": "sum",
            "Penalty_Cr": "sum"
        })
        
        cat_data["Loss_%"] = (cat_data["Penalty_Cr"] / cat_data["Revenue_Cr"]) * 100
        cat_data = cat_data[cat_data.index != "Unknown"]
        
        fig_cat = go.Figure()
        
        fig_cat.add_bar(
            y=cat_data.index,
            x=cat_data["Generation_MU"],
            name="Generation (MU)",
            orientation='h',
            marker_color='#4da6ff'
        )
        
        fig_cat.add_bar(
            y=cat_data.index,
            x=cat_data["Loss_%"],
            name="Loss %",
            orientation='h',
            marker_color='#ef4444',
            xaxis='x2'
        )
        
        fig_cat.update_layout(
            height=400,
            xaxis=dict(title="Generation (MU)", side="bottom"),
            xaxis2=dict(title="Loss %", overlaying="x", side="top"),
            yaxis_title="Category",
            template="plotly_dark",
            barmode='overlay',
            margin=dict(l=20, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_cat, use_container_width=True)
    
    st.divider()
    
    # CHART 3: QCA ANALYSIS - FORCE ALL 4 QCAs TO SHOW
    st.markdown("### 📊 QCA-wise Loss Analysis")
    
    # Load mapping to get master QCA list
    mapping_df = load_site_mapping()
    
    if mapping_df.empty:
        st.warning("⚠️ site_mapping.csv not found")
    else:
        # Get ALL QCAs from mapping (MASTER LIST - always 4)
        all_qcas_master = ['Climate Connect', 'Reconnect', 'Manikaran', 'Unilink']
        
        # Create Site→QCA mapping dictionary
        site_qca_map = dict(zip(mapping_df['Site'], mapping_df['QCA']))
        
        # Add QCA_final column to filtered data using mapping
        filtered_qca = filtered.copy()
        filtered_qca['QCA_final'] = filtered_qca['Site'].map(site_qca_map).fillna(filtered_qca.get('QCA', 'Unknown'))
        
        # Aggregate data by QCA_final
        qca_agg = filtered_qca.groupby('QCA_final').agg({
            'Actual_Revenue_INR': 'sum',
            'Total_Penalty_INR': 'sum'
        })
        
        # Create COMPLETE dataframe with ALL 4 QCAs (zeros for missing)
        qca_complete = pd.DataFrame(index=all_qcas_master)
        qca_complete['Revenue_INR'] = 0.0
        qca_complete['Penalty_INR'] = 0.0
        qca_complete['Loss_%'] = 0.0
        
        # Fill in actual data where it exists
        for qca_name in all_qcas_master:
            if qca_name in qca_agg.index:
                rev = qca_agg.loc[qca_name, 'Actual_Revenue_INR']
                pen = qca_agg.loc[qca_name, 'Total_Penalty_INR']
                qca_complete.loc[qca_name, 'Revenue_INR'] = rev
                qca_complete.loc[qca_name, 'Penalty_INR'] = pen
                if rev > 0:
                    qca_complete.loc[qca_name, 'Loss_%'] = (pen / rev) * 100
        
        # Sort by Loss %
        qca_complete = qca_complete.sort_values('Loss_%', ascending=False)
        
        st.caption(f"**Displaying ALL {len(qca_complete)} QCAs: {', '.join(qca_complete.index.tolist())}**")
        
        # Create chart (all 4 bars guaranteed)
        colors = []
        for idx, row in qca_complete.iterrows():
            if row['Revenue_INR'] == 0:
                colors.append('#808080')  # Gray - no data
            elif row['Loss_%'] > threshold:
                colors.append('#ef4444')  # Red - above threshold
            else:
                colors.append('#22c55e')  # Green - below threshold
        
        fig_qca = go.Figure()
        fig_qca.add_bar(
            x=qca_complete.index,
            y=qca_complete['Loss_%'],
            marker_color=colors,
            text=[f"{v:.2f}%" if v > 0 else "No Data" for v in qca_complete['Loss_%']],
            textposition='outside'
        )
        
        fig_qca.add_hline(y=threshold, line_dash="dash", line_color="purple",
                         annotation_text=f"Threshold: {threshold}%")
        
        fig_qca.update_layout(
            height=450,
            yaxis_title="Commercial Loss %",
            xaxis_title="QCA",
            template="plotly_dark",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_qca, use_container_width=True)
        
        # QCA Table (all 4 rows guaranteed)
        st.markdown("#### QCA Breakdown")
        
        qca_table = qca_complete.copy()
        qca_table['Revenue (Cr)'] = qca_table['Revenue_INR'] / 10_000_000
        qca_table['Penalty (L)'] = qca_table['Penalty_INR'] / 100_000
        qca_table = qca_table[['Revenue (Cr)', 'Penalty (L)', 'Loss_%']].reset_index()
        qca_table.columns = ['QCA', 'Revenue (Cr)', 'Penalty (L)', 'Loss_%']
        
        def color_cell(val):
            if pd.isna(val) or val == 0:
                return 'background-color: #404040; color: #999999'
            elif val > threshold:
                return 'background-color: #5f1e1e; color: #ff6b6b'
            else:
                return 'background-color: #1e5f3a; color: #6bffa3'
        
        styled = qca_table.style.applymap(color_cell, subset=['Loss_%']).format({
            'Revenue (Cr)': '₹{:.2f}',
            'Penalty (L)': '₹{:.2f}',
            'Loss_%': '{:.2f}%'
        })
        
        st.dataframe(styled, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # STATE RISK SUMMARY TABLE
    st.markdown("### 📋 State Risk Summary")
    
    state_table = filtered.groupby("State").agg({
        "Revenue_Cr": "sum",
        "Penalty_L": "sum",
        "Generation_MU": "sum"
    }).reset_index()
    
    state_table["Loss_%"] = (state_table["Penalty_L"] * 100_000) / (state_table["Revenue_Cr"] * 10_000_000) * 100
    state_table = state_table[state_table["State"] != "Unknown"].sort_values("Loss_%", ascending=False)
    
    state_table_display = state_table.rename(columns={
        "State": "STATE",
        "Revenue_Cr": "REVENUE (₹L)",
        "Penalty_L": "PENALTY (₹L)",
        "Loss_%": "LOSS %"
    })
    
    state_table_display["REVENUE (₹L)"] = state_table_display["REVENUE (₹L)"] * 100
    
    def color_loss(val):
        if val > threshold:
            return 'background-color: #5f1e1e; color: #ff6b6b'
        elif val > threshold/2:
            return 'background-color: #5f4a1e; color: #ffd93d'
        else:
            return 'background-color: #1e5f3a; color: #6bffa3'
    
    styled_table = state_table_display.style.applymap(
        color_loss, 
        subset=['LOSS %']
    ).format({
        'REVENUE (₹L)': '₹{:.1f} L',
        'PENALTY (₹L)': '₹{:.1f} L',
        'LOSS %': '{:.2f}%'
    })
    
    st.dataframe(styled_table, use_container_width=True, hide_index=True)
    
    # SUMMARY METRICS
    st.divider()
    st.markdown("### 📊 Portfolio Summary")
    
    sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
    
    with sum_col1:
        total_sites = len(filtered["Site"].unique())
        st.metric("Total Sites", total_sites)
    
    with sum_col2:
        total_gen = filtered["Generation_MU"].sum()
        st.metric("Total Generation", f"{total_gen:.2f} MU")
    
    with sum_col3:
        total_rev = filtered["Revenue_Cr"].sum()
        st.metric("Total Revenue", f"₹{total_rev:.2f} Cr")
    
    with sum_col4:
        total_pen = filtered["Penalty_Cr"].sum()
        st.metric("Total Penalty", f"₹{total_pen:.2f} Cr")
