import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from db.db_manager import fetch_dsm_data
from data.mapping_loader import enrich_dsm_data


def render_site_drilldown():
    """Site Drilldown with Multi-Site Comparison"""
    
    st.markdown("## 🔍 Site Drilldown & Comparison")
    
    # Load data
    df = fetch_dsm_data()
    
    if df.empty:
        st.warning("⚠️ No data available. Please upload a file.")
        return
    
    df = enrich_dsm_data(df)
    
    # Data prep
    df["Date"] = pd.to_datetime(df["Month"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.sort_values("Date")
    
    df["Generation_MU"] = df["Measured_Energy_kWh"] / 1_000_000
    df["Revenue_Cr"] = df["Actual_Revenue_INR"] / 10_000_000
    df["Penalty_Cr"] = df["Total_Penalty_INR"] / 10_000_000
    df["Penalty_L"] = df["Total_Penalty_INR"] / 100_000
    
    # Calculate loss % per row
    df["Loss_%"] = (df["Total_Penalty_INR"] / df["Actual_Revenue_INR"]) * 100
    df["Loss_%"] = df["Loss_%"].fillna(0)
    
    # Get site options BEFORE tabs
    site_options = sorted(df["Site"].dropna().astype(str).unique().tolist())
    
    if not site_options:
        st.warning("⚠️ No sites found in data.")
        return
    
    # ----------------------------
    # TABS: Single Site vs Multi-Site Comparison
    # ----------------------------
    tab1, tab2 = st.tabs(["📍 Single Site Drilldown", "⚖️ Multi-Site Comparison"])
    
    # =============================
    # TAB 1: SINGLE SITE DRILLDOWN
    # =============================
    with tab1:
        st.markdown("### Select a Site for Detailed Analysis")
        
        # Create site options with plant capacity
        site_capacity_map = {}
        for site in site_options:
            site_data_temp = df[df["Site"] == site]
            if not site_data_temp.empty and "Plant_AC_Capacity" in site_data_temp.columns:
                capacity = site_data_temp["Plant_AC_Capacity"].iloc[0]
                if pd.notna(capacity):
                    site_capacity_map[site] = f"{site} ({capacity} MW)"
                else:
                    site_capacity_map[site] = site
            else:
                site_capacity_map[site] = site
        
        # Reverse map for lookup
        display_to_site = {v: k for k, v in site_capacity_map.items()}
        
        selected_site_display = st.selectbox(
            "Select Site", 
            list(site_capacity_map.values()), 
            key="single_site"
        )
        selected_site = display_to_site.get(selected_site_display, selected_site_display.split(" (")[0])
        
        site_df = df[df["Site"] == selected_site].copy()
        
        if site_df.empty:
            st.warning("No data for selected site.")
        else:
            # Site KPIs (compact)
            col1, col2, col3, col4 = st.columns(4)
            
            total_gen = site_df["Generation_MU"].sum()
            total_rev = site_df["Revenue_Cr"].sum()
            total_pen = site_df["Penalty_L"].sum()
            avg_loss = site_df["Loss_%"].mean()
            
            with col1:
                st.metric("⚡ Generation", f"{total_gen:.2f} MU")
            with col2:
                st.metric("💰 Revenue", f"₹{total_rev:.2f} Cr")
            with col3:
                st.metric("💸 Penalty", f"₹{total_pen:.2f} L")
            with col4:
                st.metric("📉 Avg Loss %", f"{avg_loss:.2f}%")
            
            # Chart and Site Info side-by-side
            chart_col, info_col = st.columns([7, 3])
            
            with chart_col:
                st.markdown("#### 📈 Monthly Trend")
                
                monthly_df = site_df.groupby("Date").agg({
                    "Revenue_Cr": "sum",
                    "Penalty_L": "sum",
                    "Loss_%": "mean"
                }).reset_index()
                
                fig_single = go.Figure()
                
                # Revenue
                fig_single.add_bar(
                    x=monthly_df["Date"],
                    y=monthly_df["Revenue_Cr"] * 100,
                    name="Revenue (Lakh)",
                    marker_color="#4da6ff",
                    yaxis="y"
                )
                
                # Penalty
                fig_single.add_bar(
                    x=monthly_df["Date"],
                    y=monthly_df["Penalty_L"],
                    name="Penalty (Lakh)",
                    marker_color="#ef4444",
                    yaxis="y"
                )
                
                # Loss % line (green/red)
                loss_colors_single = ['rgb(34, 197, 94)' if l <= 1.0 else 'rgb(239, 68, 68)' 
                                     for l in monthly_df["Loss_%"]]
                
                fig_single.add_scatter(
                    x=monthly_df["Date"],
                    y=monthly_df["Loss_%"],
                    mode="lines+markers",
                    name="Commercial Loss %",
                    line=dict(width=3),
                    marker=dict(size=8, color=loss_colors_single),
                    yaxis="y2"
                )
                
                # Threshold lines (on secondary y-axis)
                threshold_val = st.session_state.get("threshold", 5.0)
                
                # Add threshold as scatter trace (to control which axis)
                fig_single.add_scatter(
                    x=[monthly_df["Date"].min(), monthly_df["Date"].max()],
                    y=[threshold_val, threshold_val],
                    mode="lines",
                    name=f"Threshold ({threshold_val}%)",
                    line=dict(dash="dash", color="purple", width=2),
                    yaxis="y2",
                    showlegend=True
                )
                
                # 1% critical threshold
                fig_single.add_scatter(
                    x=[monthly_df["Date"].min(), monthly_df["Date"].max()],
                    y=[1.0, 1.0],
                    mode="lines",
                    name="1% Threshold",
                    line=dict(dash="dot", color="red", width=2),
                    yaxis="y2",
                    showlegend=True
                )
                
                fig_single.update_layout(
                    height=450,
                    xaxis_title="Month",
                    yaxis=dict(title="₹ Lakh", side="left"),
                    yaxis2=dict(title="Loss %", overlaying="y", side="right"),
                    template="plotly_dark",
                    barmode="group",
                    hovermode="x unified",
                    margin=dict(l=20, r=20, t=20, b=40)
                )
                
                st.plotly_chart(fig_single, use_container_width=True)
            
            with info_col:
                st.markdown("#### 📋 Site Information")
                
                # Data points explanation
                data_points = len(site_df)
                st.metric("📊 Data Points", data_points, 
                         help="Number of monthly records available for this site")
                
                # Site metadata
                metadata_display = {}
                
                if "Technology" in site_df.columns and pd.notna(site_df["Technology"].iloc[0]):
                    metadata_display["Technology"] = site_df["Technology"].iloc[0]
                
                if "Connectivity" in site_df.columns and pd.notna(site_df["Connectivity"].iloc[0]):
                    metadata_display["Connectivity"] = site_df["Connectivity"].iloc[0]
                
                if "Power_Sale_Category" in site_df.columns and pd.notna(site_df["Power_Sale_Category"].iloc[0]):
                    metadata_display["Category"] = site_df["Power_Sale_Category"].iloc[0]
                
                if "State" in site_df.columns and pd.notna(site_df["State"].iloc[0]):
                    metadata_display["State"] = site_df["State"].iloc[0]
                
                if "QCA" in site_df.columns and pd.notna(site_df["QCA"].iloc[0]):
                    metadata_display["QCA"] = site_df["QCA"].iloc[0]
                
                if "Plant_AC_Capacity" in site_df.columns and pd.notna(site_df["Plant_AC_Capacity"].iloc[0]):
                    metadata_display["Plant AC Capacity (MW)"] = f"{site_df['Plant_AC_Capacity'].iloc[0]:.2f}"
                
                if "PPA_Rate" in site_df.columns and pd.notna(site_df["PPA_Rate"].iloc[0]):
                    metadata_display["PPA Rate"] = f"₹{site_df['PPA_Rate'].iloc[0]:.2f}"
                
                # Display as clean list
                for key, value in metadata_display.items():
                    st.markdown(f"**{key}:** {value}")

    
    # =============================
    # TAB 2: MULTI-SITE COMPARISON
    # =============================
    with tab2:
        st.markdown("### Compare Multiple Sites")
        
        # Initialize session state for selected sites
        if 'comparison_sites' not in st.session_state:
            st.session_state.comparison_sites = []
        
        # Site selector
        col_select, col_add = st.columns([4, 1])
        
        with col_select:
            new_site = st.selectbox(
                "Select Site to Add",
                [s for s in site_options if s not in st.session_state.comparison_sites],
                key="site_selector"
            )
        
        with col_add:
            st.write("")  # Spacing
            if st.button("➕ Add Site", use_container_width=True):
                if new_site and new_site not in st.session_state.comparison_sites:
                    st.session_state.comparison_sites.append(new_site)
                    st.rerun()
        
        # Display selected sites with remove buttons
        if st.session_state.comparison_sites:
            st.markdown("#### Selected Sites:")
            
            for i, site in enumerate(st.session_state.comparison_sites):
                col1, col2 = st.columns([5, 1])
                col1.write(f"**{i+1}.** {site}")
                if col2.button("✖️", key=f"remove_{i}"):
                    st.session_state.comparison_sites.pop(i)
                    st.rerun()
            
            if st.button("🗑️ Clear All"):
                st.session_state.comparison_sites = []
                st.rerun()
            
            st.markdown("---")
            
            # Filter data for selected sites
            comparison_df = df[df["Site"].isin(st.session_state.comparison_sites)].copy()
            
            if comparison_df.empty:
                st.warning("No data for selected sites.")
            else:
                # ----------------------------
                # COMPARISON KPI CARDS
                # ----------------------------
                st.markdown("#### 📊 Site Comparison Summary")
                
                site_summary = comparison_df.groupby("Site").agg({
                    "Generation_MU": "sum",
                    "Revenue_Cr": "sum",
                    "Penalty_L": "sum",
                    "Loss_%": "mean"
                }).reset_index()
                
                # Display as table
                site_summary_display = site_summary.rename(columns={
                    "Site": "SITE",
                    "Generation_MU": "GENERATION (MU)",
                    "Revenue_Cr": "REVENUE (₹Cr)",
                    "Penalty_L": "PENALTY (₹L)",
                    "Loss_%": "LOSS %"
                })
                
                st.dataframe(
                    site_summary_display.style.format({
                        "GENERATION (MU)": "{:.2f}",
                        "REVENUE (₹Cr)": "₹{:.2f}",
                        "PENALTY (₹L)": "₹{:.2f}",
                        "LOSS %": "{:.2f}%"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                st.markdown("---")
                
                # ----------------------------
                # MULTI-LINE LOSS % TREND
                # ----------------------------
                st.markdown("#### 📈 Commercial Loss % Trend Comparison")
                
                fig_multi_loss = go.Figure()
                
                colors = ['#4da6ff', '#ef4444', '#22c55e', '#f59e0b', '#a855f7', '#ec4899']
                
                for i, site in enumerate(st.session_state.comparison_sites):
                    site_data = comparison_df[comparison_df["Site"] == site]
                    monthly = site_data.groupby("Date")["Loss_%"].mean().reset_index()
                    
                    fig_multi_loss.add_scatter(
                        x=monthly["Date"],
                        y=monthly["Loss_%"],
                        mode="lines+markers",
                        name=site,
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=6)
                    )
                
                # Threshold line
                fig_multi_loss.add_hline(
                    y=1.0,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="1% Threshold"
                )
                
                fig_multi_loss.update_layout(
                    height=400,
                    xaxis_title="Month",
                    yaxis_title="Commercial Loss %",
                    template="plotly_dark",
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig_multi_loss, use_container_width=True)
                
                st.markdown("---")
                
                # ----------------------------
                # MULTI-BAR REVENUE COMPARISON
                # ----------------------------
                st.markdown("#### 💰 Revenue Comparison (₹ Lakh)")
                
                fig_multi_rev = go.Figure()
                
                for i, site in enumerate(st.session_state.comparison_sites):
                    site_data = comparison_df[comparison_df["Site"] == site]
                    monthly = site_data.groupby("Date")["Revenue_Cr"].sum().reset_index()
                    monthly["Revenue_L"] = monthly["Revenue_Cr"] * 100
                    
                    fig_multi_rev.add_bar(
                        x=monthly["Date"],
                        y=monthly["Revenue_L"],
                        name=site,
                        marker_color=colors[i % len(colors)]
                    )
                
                fig_multi_rev.update_layout(
                    height=400,
                    xaxis_title="Month",
                    yaxis_title="Revenue (₹ Lakh)",
                    template="plotly_dark",
                    barmode="group",
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig_multi_rev, use_container_width=True)
                
                st.markdown("---")
                
                # ----------------------------
                # PERFORMANCE RADAR CHART
                # ----------------------------
                st.markdown("#### 🎯 Performance Radar")
                
                # Normalize metrics for radar chart (0-100 scale)
                max_gen = site_summary["Generation_MU"].max()
                max_rev = site_summary["Revenue_Cr"].max()
                min_loss = site_summary["Loss_%"].min()
                max_loss = site_summary["Loss_%"].max()
                
                fig_radar = go.Figure()
                
                for i, site in enumerate(st.session_state.comparison_sites):
                    site_row = site_summary[site_summary["Site"] == site].iloc[0]
                    
                    # Normalize (higher is better, so invert loss %)
                    gen_norm = (site_row["Generation_MU"] / max_gen) * 100 if max_gen > 0 else 0
                    rev_norm = (site_row["Revenue_Cr"] / max_rev) * 100 if max_rev > 0 else 0
                    loss_norm = 100 - ((site_row["Loss_%"] - min_loss) / (max_loss - min_loss + 0.01)) * 100
                    
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[gen_norm, rev_norm, loss_norm, 
                           (gen_norm + rev_norm + loss_norm) / 3],  # Overall score
                        theta=['Generation', 'Revenue', 'Low Loss', 'Overall'],
                        fill='toself',
                        name=site,
                        marker_color=colors[i % len(colors)]
                    ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100])
                    ),
                    height=500,
                    template="plotly_dark",
                    showlegend=True
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
        
        else:
            st.info("👆 Add sites above to start comparison")
