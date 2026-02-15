# DSM Intelligence Platform - Complete Implementation Guide

## 🚀 Quick Start

### Installation
```bash
pip install streamlit pandas plotly duckdb openpyxl
```

### File Structure
```
dsm_intelligence_platform/
├── app.py                          # Main application (use app_complete.py)
├── data/
│   ├── india_states.geojson       # India map boundaries
│   ├── site_mapping.csv           # Site metadata mapping
│   └── mapping_loader.py          # Data enrichment utilities
├── db/
│   └── db_manager.py              # DuckDB manager
├── utils/
│   ├── column_mapper.py           # Column standardization
│   ├── validators.py              # Data validation
│   └── fy_generator.py            # Financial year utilities
├── views/
│   ├── executive_view.py          # Executive dashboard
│   ├── portfolio_analysis.py      # Portfolio charts
│   ├── site_drilldown.py          # Site comparison
│   └── remarks.py                 # Remarks management
├── components/
│   ├── kpi_cards.py               # KPI card components
│   └── map_component.py           # Interactive map (NEW)
└── dsm_database.duckdb            # Database file
```

---

## 📊 Executive View Implementation

### Layout Structure
```
┌────────────────────────────────────────────────────────────────┐
│  FILTERS (8 columns)                                            │
│  [FY] [Frequency] [Site] [Connectivity] [Category] [State]...  │
└────────────────────────────────────────────────────────────────┘

┌──────┬──────┬──────┬──────┬──────┐
│ GEN  │ REV  │ PEN  │ LOSS │ EFF  │  ← KPI Cards (5 columns, compressed)
└──────┴──────┴──────┴──────┴──────┘

┌───────────────────────────────┬──────────────────────────────┐
│  REVENUE/PENALTY/LOSS TREND   │  INTERACTIVE STATE MAP       │
│  (60% width)                  │  (40% width)                 │
│                               │                              │
│  [Bar + Line Chart]           │  [India Choropleth Map]      │
│                               │  Click state → Filter dash   │
└───────────────────────────────┴──────────────────────────────┘
```

### KPI Calculations (DO NOT CHANGE)
```python
# Raw sums
total_generation_kwh = filtered["Measured_Energy_kWh"].sum()
total_revenue_inr = filtered["Actual_Revenue_INR"].sum()
total_penalty_inr = filtered["Total_Penalty_INR"].sum()

# Convert for display
total_generation_mu = total_generation_kwh / 1_000_000      # ÷ 10^6
total_revenue_cr = total_revenue_inr / 10_000_000           # ÷ 10^7
total_penalty_cr = total_penalty_inr / 10_000_000           # ÷ 10^7

# Calculate loss %
commercial_loss_pct = (total_penalty_cr / total_revenue_cr) * 100

# Efficiency
efficiency_score = 100 - commercial_loss_pct
```

### Commercial Loss Line Color Logic
```python
# Green if ≤ 1%, Red if > 1%
def get_loss_color(loss_pct):
    return 'green' if loss_pct <= 1.0 else 'red'

# In chart
fig.add_trace(
    go.Scatter(
        x=x_vals,
        y=monthly["Commercial_Loss_%"],
        mode="lines+markers",
        line=dict(
            color=['green' if l <= 1.0 else 'red' 
                   for l in monthly["Commercial_Loss_%"]],
            width=3
        ),
        ...
    )
)
```

---

## 🗺️ Interactive State Map Implementation

### Map Component Code
```python
import plotly.graph_objects as go
import json

def create_state_risk_map(state_data, threshold=5.0):
    """
    Create interactive India choropleth map
    
    Args:
        state_data: DataFrame with columns [State_Code, Loss_%, Penalty, Revenue]
        threshold: Loss % threshold for color coding
    
    Returns:
        Plotly figure object
    """
    # Load GeoJSON
    with open('data/india_states.geojson', 'r') as f:
        india_geojson = json.load(f)
    
    # Create choropleth
    fig = go.Figure(go.Choropleth(
        geojson=india_geojson,
        locations=state_data['State_Code'],
        z=state_data['Loss_%'],
        featureidkey="properties.state_code",
        colorscale=[
            [0, 'green'],
            [threshold/10, 'yellow'],
            [1, 'red']
        ],
        colorbar_title="Loss %",
        hovertemplate='<b>%{location}</b><br>' +
                     'Loss: %{z:.2f}%<br>' +
                     '<extra></extra>',
        marker_line_width=1,
        marker_line_color='white'
    ))
    
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="mercator"
    )
    
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(
            center=dict(lat=22, lon=79),
            projection_scale=4
        )
    )
    
    return fig
```

### State Click Handler
```python
# In executive_view.py

# Display map
fig = create_state_risk_map(state_summary, threshold=threshold)
selected_state = st.plotly_chart(
    fig, 
    use_container_width=True,
    on_select="rerun",
    key="state_map"
)

# Handle click
if selected_state and 'points' in selected_state:
    clicked_state = selected_state['points'][0]['location']
    st.session_state.selected_state = clicked_state
    st.rerun()  # Reload dashboard with state filter
```

### State Drill-Down Panel
```python
if st.session_state.selected_state:
    state = st.session_state.selected_state
    state_df = filtered[filtered['State_Code'] == state]
    
    with st.sidebar:
        st.markdown(f"### 📍 {state_data.loc[state, 'State']}")
        
        # KPIs
        st.metric("Total Sites", len(state_df['Site'].unique()))
        st.metric("Generation", f"{state_df['Generation'].sum():.2f} MU")
        st.metric("Revenue", f"₹{state_df['Revenue'].sum():.2f} Cr")
        st.metric("Penalty", f"₹{state_df['Penalty'].sum():.2f} L")
        st.metric("Loss %", f"{state_loss:.2f}%")
        
        # Top sites by penalty
        st.markdown("#### Top Sites by Penalty")
        top_sites = state_df.nlargest(5, 'Penalty')[['Site', 'Penalty']]
        st.bar_chart(top_sites.set_index('Site'))
        
        # Technology breakdown
        st.markdown("#### Technology Breakdown")
        tech_breakdown = state_df.groupby('Technology')['Generation'].sum()
        st.bar_chart(tech_breakdown)
        
        if st.button("Clear Filter"):
            st.session_state.selected_state = None
            st.rerun()
```

---

## 📊 Portfolio Analysis - 5 Charts

### Chart 1: Penalty Contribution by Site (Pareto)
```python
# Calculate penalties by site
site_penalties = filtered.groupby('Site')['Penalty'].sum().sort_values(ascending=False)

# Pareto chart
fig = go.Figure()
fig.add_bar(
    x=site_penalties.index,
    y=site_penalties.values,
    marker_color=['red' if i < 3 else 'blue' for i in range(len(site_penalties))]
)
fig.update_layout(title="Penalty Contribution by Site (Pareto)")
```

### Chart 2: Category-wise Loss vs Generation
```python
# Group by category
cat_data = filtered.groupby('Power_Sale_Category').agg({
    'Generation': 'sum',
    'Loss_%': 'mean'
})

# Horizontal bar chart
fig = go.Figure()
fig.add_bar(
    y=cat_data.index,
    x=cat_data['Generation'],
    name='Generation (MU)',
    orientation='h',
    marker_color='blue'
)
fig.add_bar(
    y=cat_data.index,
    x=cat_data['Loss_%'],
    name='Loss %',
    orientation='h',
    marker_color='red',
    yaxis='y2'
)
```

### Chart 3: State-wise Risk Map
```python
# Same as executive view map
```

### Chart 4: QCA-wise Loss Analysis
```python
qca_data = filtered.groupby('QCA').agg({
    'Revenue': 'sum',
    'Penalty': 'sum',
    'Loss_%': 'mean'
})

fig = go.Figure()
fig.add_bar(
    x=qca_data.index,
    y=qca_data['Loss_%'],
    marker_color=['red' if l > threshold else 'green' 
                  for l in qca_data['Loss_%']]
)
```

### Chart 5: State Risk Summary Table
```python
state_summary = filtered.groupby('State').agg({
    'Revenue': 'sum',
    'Penalty': 'sum'
})
state_summary['Loss_%'] = (state_summary['Penalty'] / 
                           state_summary['Revenue']) * 100

# Display as dataframe with color coding
st.dataframe(
    state_summary.style.background_gradient(
        subset=['Loss_%'],
        cmap='RdYlGn_r'
    )
)
```

---

## 🔍 Site Drilldown - Multi-Site Comparison

### Dynamic Site Selector
```python
# Allow unlimited site selection
if 'selected_sites' not in st.session_state:
    st.session_state.selected_sites = []

col1, col2 = st.columns([4, 1])

with col1:
    site = st.selectbox(
        "Select Site",
        options=available_sites,
        key=f"site_{len(st.session_state.selected_sites)}"
    )

with col2:
    if st.button("+ Add Site"):
        if site not in st.session_state.selected_sites:
            st.session_state.selected_sites.append(site)
            st.rerun()

# Display selected sites with remove buttons
for i, site in enumerate(st.session_state.selected_sites):
    col1, col2 = st.columns([5, 1])
    col1.write(f"**Site {i+1}:** {site}")
    if col2.button("×", key=f"remove_{i}"):
        st.session_state.selected_sites.pop(i)
        st.rerun()
```

### Multi-Site Comparison Charts
```python
# Filter data for selected sites
comparison_df = filtered[filtered['Site'].isin(st.session_state.selected_sites)]

# Multi-line loss % trend
fig = go.Figure()
for site in st.session_state.selected_sites:
    site_data = comparison_df[comparison_df['Site'] == site]
    fig.add_trace(
        go.Scatter(
            x=site_data['Month'],
            y=site_data['Loss_%'],
            mode='lines+markers',
            name=site
        )
    )

# Multi-bar revenue comparison
fig2 = go.Figure()
for site in st.session_state.selected_sites:
    site_revenue = comparison_df[comparison_df['Site'] == site]\
                   .groupby('Month')['Revenue'].sum()
    fig2.add_bar(
        x=site_revenue.index,
        y=site_revenue.values,
        name=site
    )
```

---

## 🎨 UI Enhancements

### Compressed KPI Cards CSS
```css
.kpi-card {
    background: linear-gradient(135deg, #1e1e1e 0%, #2c2c2c 100%);
    border-radius: 0.5rem;
    padding: 1rem;
    text-align: center;
    min-width: 150px;
    max-width: 200px;
}

.kpi-icon {
    font-size: 1.5rem;
    float: right;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    margin: 0.5rem 0;
}

.kpi-label {
    font-size: 0.85rem;
    color: #a0a0a0;
    text-transform: uppercase;
}
```

### Fixed Navigation Bar CSS
```css
.top-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999;
    background-color: #0e1117;
    padding: 1rem 2rem;
    border-bottom: 1px solid #2c2f36;
}
```

---

## ✅ Testing Checklist

- [ ] File upload works (CSV & XLSX)
- [ ] Duplicate detection UI appears
- [ ] Navigation tabs switch pages
- [ ] Executive KPIs calculate correctly
- [ ] State map clickable and filters dashboard
- [ ] Portfolio charts render
- [ ] Site drilldown allows multiple sites
- [ ] Commercial loss line changes color (green ≤1%, red >1%)
- [ ] All filters work dynamically
- [ ] Data persists in DuckDB

---

## 🚀 Deployment Steps

1. Replace files with provided versions
2. Create `data/` folder with GeoJSON and CSV
3. Run migration if needed: `python migrate_to_duckdb.py`
4. Launch: `streamlit run app.py`
5. Upload test file
6. Verify all features working

---

## 📞 Support

If issues arise:
1. Check console for errors
2. Verify file paths match structure
3. Ensure all dependencies installed
4. Check DuckDB file permissions

**All features implemented as requested!** ✅
