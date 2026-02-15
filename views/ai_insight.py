import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from components.kpi_cards import KpiCard, render_kpi_row
from components.threshold_line import add_threshold_colored_series


def render_ai_insight():
    st.markdown("## 🧠 AI Intelligence Engine")
    st.markdown("### Executive Risk & Forecast Intelligence")

    if "main_data" not in st.session_state:
        st.warning("⚠️ Please upload data in Executive View first.")
        return

    df = st.session_state.main_data.copy()

    if df.empty:
        st.warning("⚠️ Dataset is empty.")
        return

    df["Date"] = pd.to_datetime(df["Month"], errors="coerce")
    df = df.sort_values("Date")

    df["Revenue_INR"] = df["Actual_Revenue_INR"]
    df["DSM_Penalty_INR"] = df["Total_Penalty_INR"]
    df["Commercial_Loss_%"] = df["Commercial_Loss"]

    required_cols = ["Date", "Revenue_INR", "DSM_Penalty_INR", "Commercial_Loss_%"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"❌ Missing required column: {col}")
            return

    monthly = (
        df.groupby("Date")
        .agg({"Revenue_INR": "sum", "DSM_Penalty_INR": "sum", "Commercial_Loss_%": "mean"})
        .reset_index()
    )

    monthly = monthly.sort_values("Date")
    monthly["Month_Index"] = np.arange(len(monthly))

    threshold_pct = float(st.session_state.get("threshold", 5.0))

    model = LinearRegression()
    X = monthly[["Month_Index"]]
    y = monthly["Commercial_Loss_%"]

    model.fit(X, y)

    next_index = pd.DataFrame({"Month_Index": [int(monthly["Month_Index"].max()) + 1]})
    forecast_loss_pct = float(model.predict(next_index)[0])

    st.markdown("### 📉 Revenue at Risk Model")

    months_forward = st.number_input(
        "Forecast Horizon (Months)", min_value=1, max_value=24, value=st.session_state.forecast_horizon
    )

    st.session_state.forecast_horizon = months_forward

    avg_revenue = monthly["Revenue_INR"].mean()

    excess_loss_pct = max(forecast_loss_pct - threshold_pct, 0.0)
    rar = (excess_loss_pct / 100.0) * avg_revenue * months_forward

    render_kpi_row(
        [
            KpiCard("📊 Forecast Commercial Loss", f"{forecast_loss_pct:.2f}%", accent="#f59e0b"),
            KpiCard("🎯 Threshold", f"{threshold_pct:.2f}%", accent="#ef4444"),
            KpiCard("💰 Revenue at Risk (₹ Cr)", f"{rar/1e7:.2f}", accent="#22c55e"),
        ],
        columns=3,
    )

    risk_score = min(int((forecast_loss_pct / threshold_pct) * 50), 100) if threshold_pct > 0 else 100

    if forecast_loss_pct > threshold_pct:
        risk_status = "🔴 High Risk"
    elif forecast_loss_pct > threshold_pct * 0.7:
        risk_status = "🟡 Watchlist"
    else:
        risk_status = "🟢 Stable"

    st.markdown(f"### 🚦 Risk Classification: {risk_status}")
    st.markdown(f"Risk Score: **{risk_score}/100**")

    fig = go.Figure()

    add_threshold_colored_series(
        fig,
        x=monthly["Date"].tolist(),
        y=monthly["Commercial_Loss_%"].astype(float).tolist(),
        threshold=float(threshold_pct),
        yaxis="y",
        name="Historical Loss",
    )

    next_date = monthly["Date"].iloc[-1] + pd.DateOffset(months=1)

    fig.add_trace(
        go.Scatter(
            x=[next_date],
            y=[forecast_loss_pct],
            mode="markers",
            marker=dict(size=12, color="orange"),
            name="Forecast",
        )
    )

    fig.add_hline(y=threshold_pct, line_dash="dash", line_color="red", annotation_text="Threshold")

    fig.update_layout(
        title="Commercial Loss Forecast",
        xaxis_title="Date",
        yaxis_title="Commercial Loss (%)",
        height=400,
        template="plotly_dark",
    )

    st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.markdown("### 🧾 AI Executive Summary")

    if forecast_loss_pct > threshold_pct:
        st.error(
            f"""
            AI predicts breach risk.

            Forecast Loss: {forecast_loss_pct:.2f}%
            Threshold: {threshold_pct:.2f}%

            Estimated Exposure over {months_forward} months:
            ₹{rar/1e7:.2f} Cr
            """
        )
    else:
        st.success(
            f"""
            Commercial loss is expected to remain controlled.

            Forecast Loss: {forecast_loss_pct:.2f}%
            Threshold: {threshold_pct:.2f}%
            """
        )

