import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from db.db_manager import fetch_dsm_data
from data.mapping_loader import load_site_mapping, enrich_dsm_data
from utils.fy_generator import generate_financial_year, generate_financial_quarter


def render_executive_view():
    """Executive Dashboard - Full Width Chart, No Map"""
    
    # Load data
    df = fetch_dsm_data()
    
    if df.empty:
        st.warning("⚠️ No data available. Please upload a file.")
        return
    
    # Enrich with mapping data (only add missing columns, don't overwrite existing)
    df = enrich_dsm_data(df)
    
    # Data preparation
    df["Date"] = pd.to_datetime(df["Month"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.sort_values("Date")
    df["FY"] = df["Date"].dt.year.apply(lambda y: f"FY{y}")
    df["Quarter"] = generate_financial_quarter(df["Date"])
    
    # Fill ONLY if columns don't exist or have nulls (preserve raw data)
    if "QCA" not in df.columns:
        df["QCA"] = "Unknown"
    else:
        df["QCA"] = df["QCA"].fillna("Unknown")
    
    if "Connectivity" not in df.columns:
        df["Connectivity"] = "Unknown"
    else:
        df["Connectivity"] = df["Connectivity"].fillna("Unknown")
    
    if "State" not in df.columns:
        df["State"] = "Unknown"
    else:
        df["State"] = df["State"].fillna("Unknown")
    
    if "State_Code" not in df.columns:
        df["State_Code"] = "UK"
    else:
        df["State_Code"] = df["State_Code"].fillna("UK")
    
    if "Power_Sale_Category" not in df.columns:
        df["Power_Sale_Category"] = "Unknown"
    else:
        df["Power_Sale_Category"] = df["Power_Sale_Category"].fillna("Unknown")
    
    # FILTERS (2 rows for better space)
    st.markdown("### 🔍 Filters")
    
    # Row 1: Main filters
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        fy_options = sorted(df["FY"].dropna().unique())
        fy = st.multiselect("FY", fy_options, key="exec_fy")
    
    with col2:
        frequency = st.selectbox("Frequency", ["Month", "Quarter"], key="exec_freq")
    
    with col3:
        site_options = sorted(df["Site"].dropna().astype(str).unique().tolist())
        site = st.selectbox("Site", ["All"] + site_options, key="exec_site")
    
    with col4:
        conn_options = sorted(df["Connectivity"].dropna().astype(str).unique().tolist())
        connectivity = st.selectbox("Connectivity", ["All"] + conn_options, key="exec_conn")
    
    with col5:
        cat_options = [c for c in sorted(df["Power_Sale_Category"].dropna().astype(str).unique().tolist()) 
                       if c and c != "Unknown"]
        category = st.selectbox("Category", ["All"] + cat_options, key="exec_cat")
    
    # Row 2: Additional filters
    col6, col7, col8, col9 = st.columns(4)
    
    with col6:
        # QCA Filter
        qca_options = [q for q in sorted(df["QCA"].dropna().astype(str).unique().tolist()) 
                      if q and q != "Unknown"]
        qca = st.selectbox("QCA", ["All"] + qca_options, key="exec_qca")
    
    with col7:
        state_options = [s for s in sorted(df["State"].dropna().astype(str).unique().tolist()) 
                        if s and s != "Unknown"]
        state = st.selectbox("State", ["All"] + state_options, key="exec_state")
    
    with col8:
        threshold = st.number_input("Threshold %", value=5.0, step=0.5, key="exec_thresh")
        st.session_state["threshold"] = threshold
    
    with col9:
        st.write("")
        if st.button("🔄 Reset", key="exec_reset", use_container_width=True):
            st.session_state.selected_state = None
            st.rerun()
    
    # Apply filters
    filtered = df.copy()
    if fy:
        filtered = filtered[filtered["FY"].isin(fy)]
    if site != "All":
        filtered = filtered[filtered["Site"].astype(str) == str(site)]
    if connectivity != "All":
        filtered = filtered[filtered["Connectivity"].astype(str) == str(connectivity)]
    if category != "All":
        filtered = filtered[filtered["Power_Sale_Category"].astype(str) == str(category)]
    if qca != "All":
        filtered = filtered[filtered["QCA"].astype(str) == str(qca)]
    if state != "All":
        filtered = filtered[filtered["State"].astype(str) == str(state)]
    
    if filtered.empty:
        st.warning("⚠️ No data matches selected filters.")
        return
    
    st.divider()
    
    # KPI CARDS
    total_generation_kwh = filtered["Measured_Energy_kWh"].sum()
    total_revenue_inr = filtered["Actual_Revenue_INR"].sum()
    total_penalty_inr = filtered["Total_Penalty_INR"].sum()
    
    total_generation_mu = total_generation_kwh / 1_000_000
    total_revenue_cr = total_revenue_inr / 10_000_000
    total_penalty_cr = total_penalty_inr / 10_000_000
    
    if total_revenue_cr > 0:
        commercial_loss_pct = (total_penalty_cr / total_revenue_cr) * 100
    else:
        commercial_loss_pct = 0.0
    
    efficiency_score = 100 - commercial_loss_pct
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2a5298 100%); 
                    border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 12px; color: #a0a0a0; text-transform: uppercase;">⚡ Total Generation</div>
            <div style="font-size: 28px; font-weight: 700; color: #4da6ff; margin: 10px 0;">{total_generation_mu:.2f}</div>
            <div style="font-size: 14px; color: #cccccc;">MU</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e5f3a 0%, #2a9852 100%); 
                    border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 12px; color: #a0a0a0; text-transform: uppercase;">💰 Total Revenue</div>
            <div style="font-size: 28px; font-weight: 700; color: #22c55e; margin: 10px 0;">₹{total_revenue_cr:.2f}</div>
            <div style="font-size: 14px; color: #cccccc;">Cr</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #5f1e1e 0%, #982a2a 100%); 
                    border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 12px; color: #a0a0a0; text-transform: uppercase;">💸 DSM Penalty</div>
            <div style="font-size: 28px; font-weight: 700; color: #ef4444; margin: 10px 0;">₹{total_penalty_cr:.2f}</div>
            <div style="font-size: 14px; color: #cccccc;">Cr</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        loss_color = "#ef4444" if commercial_loss_pct > 1.0 else "#22c55e"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #5f4a1e 0%, #98762a 100%); 
                    border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 12px; color: #a0a0a0; text-transform: uppercase;">⚖️ Commercial Loss</div>
            <div style="font-size: 28px; font-weight: 700; color: {loss_color}; margin: 10px 0;">{commercial_loss_pct:.2f}</div>
            <div style="font-size: 14px; color: #cccccc;">%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi5:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4a1e5f 0%, #762a98 100%); 
                    border-radius: 10px; padding: 20px; text-align: center;">
            <div style="font-size: 12px; color: #a0a0a0; text-transform: uppercase;">🎯 Efficiency Score</div>
            <div style="font-size: 28px; font-weight: 700; color: #a855f7; margin: 10px 0;">{efficiency_score:.2f}</div>
            <div style="font-size: 14px; color: #cccccc;">Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # FULL WIDTH CHART (NO MAP)
    st.markdown("### 📈 Revenue, Penalty & Commercial Loss Trend")
    
    # Aggregate data
    if frequency == "Quarter":
        monthly = filtered.groupby(["FY", "Quarter", "Date"]).agg({
            "Actual_Revenue_INR": "sum",
            "Total_Penalty_INR": "sum",
        }).reset_index()
        monthly = monthly.sort_values("Date")
        monthly["Period"] = monthly["Quarter"] + " " + monthly["FY"]
        x_vals = monthly["Period"]
    else:
        monthly = filtered.groupby("Date").agg({
            "Actual_Revenue_INR": "sum",
            "Total_Penalty_INR": "sum",
        }).reset_index()
        monthly = monthly.sort_values("Date")
        x_vals = monthly["Date"]
    
    monthly["Commercial_Loss_%"] = (monthly["Total_Penalty_INR"] / monthly["Actual_Revenue_INR"]) * 100
    monthly["Commercial_Loss_%"] = monthly["Commercial_Loss_%"].fillna(0)
    
    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Bar(
        x=x_vals,
        y=monthly["Actual_Revenue_INR"] / 100_000,
        name="Revenue (Lakh)",
        marker_color="#4da6ff",
        yaxis="y"
    ))
    
    fig_trend.add_trace(go.Bar(
        x=x_vals,
        y=monthly["Total_Penalty_INR"] / 100_000,
        name="Penalty (Lakh)",
        marker_color="#ff4d4d",
        yaxis="y"
    ))
    
    # Commercial Loss line (GREEN ≤1%, RED >1%)
    loss_line_colors = ['rgb(34, 197, 94)' if l <= 1.0 else 'rgb(239, 68, 68)' 
                       for l in monthly["Commercial_Loss_%"]]
    
    fig_trend.add_trace(go.Scatter(
        x=x_vals,
        y=monthly["Commercial_Loss_%"],
        mode="lines+markers",
        name="Commercial Loss %",
        line=dict(width=3),
        marker=dict(size=8, color=loss_line_colors, line=dict(width=2, color='white')),
        yaxis="y2"
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=x_vals,
        y=[threshold] * len(monthly),
        mode="lines",
        name="Threshold",
        line=dict(color="purple", dash="dash", width=2),
        yaxis="y2"
    ))
    
    fig_trend.update_layout(
        height=500,
        xaxis=dict(title="Period"),
        yaxis=dict(title="₹ Lakh", side="left"),
        yaxis2=dict(title="Commercial Loss %", overlaying="y", side="right", 
                   range=[0, max(threshold * 2, monthly["Commercial_Loss_%"].max() * 1.2)]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark",
        barmode="group",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=20, b=40)
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.session_state.main_data = filtered
