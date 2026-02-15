# KPI Calculation Reference - Executive View

## 📊 Complete Formula Breakdown

### Data Flow: Excel → Database → KPI Display

```
Excel Column F: "Measured Energy kWh"
    ↓ (uploaded)
Database Column: Measured_Energy_kWh (raw kWh values)
    ↓ (SUM filtered rows)
Raw Total: 12,345,678 kWh
    ↓ (÷ 10^6)
Display: 12.35 MU
```

---

## 🎯 KPI Formulas (Step-by-Step)

### 1. Total Generation (MU)

**Source Column:** Column F → `Measured_Energy_kWh`

**Calculation:**
```python
# Step 1: Sum raw kWh values from filtered data
total_generation_kwh = SUM(Measured_Energy_kWh)

# Step 2: Convert to MU (Million Units)
total_generation_mu = total_generation_kwh / 1,000,000  # Divide by 10^6

# Display
"12.35 MU"
```

**Conversion Factor:**
- **kWh to MU:** ÷ 10^6 (1,000,000)
- **kWh to GWh:** ÷ 10^3 (1,000)

**Example:**
```
Raw data: 12,345,678 kWh
Calculation: 12,345,678 ÷ 1,000,000 = 12.35 MU
Display: "12.35 MU"
```

---

### 2. Total Revenue (Cr)

**Source Column:** Column I → `Actual_Revenue_INR`

**Calculation:**
```python
# Step 1: Sum raw INR values from filtered data
total_revenue_inr = SUM(Actual_Revenue_INR)

# Step 2: Convert to Crores
total_revenue_cr = total_revenue_inr / 10,000,000  # Divide by 10^7

# Display
"₹45.67 Cr"
```

**Conversion Factor:**
- **INR to Crores:** ÷ 10^7 (10,000,000)
- **INR to Lakhs:** ÷ 10^5 (100,000)

**Example:**
```
Raw data: ₹456,789,123 INR
Calculation: 456,789,123 ÷ 10,000,000 = 45.68 Cr
Display: "₹45.68 Cr"
```

---

### 3. DSM Penalty (Cr)

**Source Column:** Column J → `Total_Penalty_INR`

**Calculation:**
```python
# Step 1: Sum raw INR values from filtered data
total_penalty_inr = SUM(Total_Penalty_INR)

# Step 2: Convert to Crores
total_penalty_cr = total_penalty_inr / 10,000,000  # Divide by 10^7

# Display
"₹2.34 Cr"
```

**Conversion Factor:**
- **INR to Crores:** ÷ 10^7 (10,000,000)
- **INR to Lakhs:** ÷ 10^5 (100,000)

**Example:**
```
Raw data: ₹23,456,789 INR
Calculation: 23,456,789 ÷ 10,000,000 = 2.35 Cr
Display: "₹2.35 Cr"
```

---

### 4. Commercial Loss (%)

**Source:** Calculated from KPI values (Crores)

**🔥 CRITICAL: Use Crore values from KPIs, NOT raw INR**

**Calculation:**
```python
# Step 1: Get converted values from KPIs
total_penalty_cr = 2.35 Cr  # From KPI #3
total_revenue_cr = 45.68 Cr # From KPI #2

# Step 2: Calculate percentage
commercial_loss_pct = (total_penalty_cr / total_revenue_cr) × 100

# Display
"5.14%"
```

**Formula:**
```
Commercial Loss % = (DSM Penalty Cr / Total Revenue Cr) × 100
```

**Example:**
```
DSM Penalty: ₹2.35 Cr
Total Revenue: ₹45.68 Cr
Calculation: (2.35 / 45.68) × 100 = 5.14%
Display: "5.14%"
```

**⚠️ Important:** Do NOT use raw INR values for this calculation. Use the Crore values already calculated in KPIs #2 and #3.

---

### 5. Efficiency Score

**Source:** Calculated from Commercial Loss %

**Calculation:**
```python
# Step 1: Get Commercial Loss % from KPI #4
commercial_loss_pct = 5.14%

# Step 2: Calculate efficiency
efficiency_score = 100 - commercial_loss_pct

# Display
"94.86"
```

**Formula:**
```
Efficiency Score = 100 - Commercial Loss %
```

**Example:**
```
Commercial Loss: 5.14%
Calculation: 100 - 5.14 = 94.86
Display: "94.86"
```

---

## 📐 Conversion Reference Table

### Energy Conversions

| From | To | Divide By | Example |
|------|-----|-----------|---------|
| kWh | MWh | 10^3 (1,000) | 12,345 kWh = 12.35 MWh |
| kWh | GWh | 10^6 (1,000,000) | 12,345,678 kWh = 12.35 GWh |
| kWh | MU | 10^6 (1,000,000) | 12,345,678 kWh = 12.35 MU |
| MWh | GWh | 10^3 (1,000) | 12,345 MWh = 12.35 GWh |

### Currency Conversions

| From | To | Divide By | Example |
|------|-----|-----------|---------|
| INR | Thousand | 10^3 (1,000) | ₹12,345 = ₹12.35 K |
| INR | Lakh | 10^5 (100,000) | ₹12,34,567 = ₹12.35 Lakh |
| INR | Crore | 10^7 (10,000,000) | ₹12,34,56,789 = ₹12.35 Cr |

---

## 🔄 Complete Calculation Flow

### Example with Real Data

**Filtered Dataset (3 months):**

| Month | Site | Measured_Energy_kWh | Actual_Revenue_INR | Total_Penalty_INR |
|-------|------|---------------------|-------------------|------------------|
| Jan-25 | WASHI | 5,000,000 | 150,000,000 | 7,500,000 |
| Feb-25 | WASHI | 4,500,000 | 135,000,000 | 6,750,000 |
| Mar-25 | WASHI | 5,500,000 | 165,000,000 | 8,250,000 |

**Step-by-Step Calculation:**

**1. Total Generation (MU)**
```
Sum kWh = 5,000,000 + 4,500,000 + 5,500,000 = 15,000,000 kWh
Convert to MU = 15,000,000 ÷ 1,000,000 = 15.00 MU
Display: "15.00 MU"
```

**2. Total Revenue (Cr)**
```
Sum INR = 150,000,000 + 135,000,000 + 165,000,000 = 450,000,000 INR
Convert to Cr = 450,000,000 ÷ 10,000,000 = 45.00 Cr
Display: "₹45.00 Cr"
```

**3. DSM Penalty (Cr)**
```
Sum INR = 7,500,000 + 6,750,000 + 8,250,000 = 22,500,000 INR
Convert to Cr = 22,500,000 ÷ 10,000,000 = 2.25 Cr
Display: "₹2.25 Cr"
```

**4. Commercial Loss (%)**
```
Use KPI values (Crores):
Penalty = 2.25 Cr
Revenue = 45.00 Cr
Loss % = (2.25 / 45.00) × 100 = 5.00%
Display: "5.00%"
```

**5. Efficiency Score**
```
Efficiency = 100 - 5.00 = 95.00
Display: "95.00"
```

---

## 🎯 Filter Impact on KPIs

### All KPIs Recalculate Dynamically

**Example: Filter by Site = "WASHI"**

```python
# Before filtering (all data)
Total Generation: 50.00 MU
Total Revenue: ₹150.00 Cr
DSM Penalty: ₹7.50 Cr
Commercial Loss: 5.00%

# After filtering (only WASHI)
Total Generation: 15.00 MU  ← Recalculated
Total Revenue: ₹45.00 Cr    ← Recalculated
DSM Penalty: ₹2.25 Cr       ← Recalculated
Commercial Loss: 5.00%      ← Recalculated
```

### Filter Combinations

**FY2025 + Site WASHI:**
- Filters dataset to only FY2025 and WASHI rows
- All KPIs recalculate from filtered subset

**FY2025 + Category "Climate Connect":**
- Filters dataset to only FY2025 and Climate Connect QCA
- All KPIs recalculate from filtered subset

---

## 🔍 Verification Checklist

### Manual Verification Steps

**Test 1: Check Generation Conversion**
```
1. Open your Excel file
2. Filter to your date range
3. Sum column F (Measured Energy kWh)
4. Divide by 1,000,000
5. Should match "Total Generation" KPI
```

**Test 2: Check Revenue Conversion**
```
1. Sum column I (Actual Revenue INR)
2. Divide by 10,000,000
3. Should match "Total Revenue" KPI
```

**Test 3: Check Penalty Conversion**
```
1. Sum column J (Total Penalty INR)
2. Divide by 10,000,000
3. Should match "DSM Penalty" KPI
```

**Test 4: Check Commercial Loss Formula**
```
1. Take "DSM Penalty" KPI value (in Cr)
2. Take "Total Revenue" KPI value (in Cr)
3. Calculate: (Penalty Cr / Revenue Cr) × 100
4. Should match "Commercial Loss" KPI
```

---

## 🛠️ Troubleshooting

### Issue: KPI values too small

**Problem:** Generation shows 0.01 MU instead of 10.00 MU

**Cause:** Data in Excel is already in MU, not kWh

**Fix:** Check your Excel column F - if values are already small (like 10, 20), they're already in MU. Remove the division.

---

### Issue: KPI values too large

**Problem:** Revenue shows ₹45,678.90 Cr instead of ₹45.68 Cr

**Cause:** Data in Excel is already in Crores, not INR

**Fix:** Check your Excel columns I & J - if values are already small (like 45, 2), they're already in Crores. Remove the division.

---

### Issue: Commercial Loss % incorrect

**Problem:** Shows 0.05% instead of 5.00%

**Cause:** Using raw INR values instead of Crore values

**Fix:** Ensure formula uses Crore values from KPIs:
```python
# ✅ CORRECT
commercial_loss_pct = (total_penalty_cr / total_revenue_cr) × 100

# ❌ WRONG
commercial_loss_pct = (total_penalty_inr / total_revenue_inr) × 100
```

---

## 📝 Code Reference

### Python Implementation

```python
# RAW VALUES (from filtered data)
total_generation_kwh = filtered["Measured_Energy_kWh"].sum()
total_revenue_inr = filtered["Actual_Revenue_INR"].sum()
total_penalty_inr = filtered["Total_Penalty_INR"].sum()

# CONVERT FOR DISPLAY
total_generation_mu = total_generation_kwh / 1_000_000      # ÷ 10^6
total_revenue_cr = total_revenue_inr / 10_000_000           # ÷ 10^7
total_penalty_cr = total_penalty_inr / 10_000_000           # ÷ 10^7

# CALCULATE PERCENTAGES (using Crore values)
if total_revenue_cr > 0:
    commercial_loss_pct = (total_penalty_cr / total_revenue_cr) * 100
else:
    commercial_loss_pct = 0.0

efficiency_score = 100 - commercial_loss_pct

# DISPLAY
KpiCard("⚡ Total Generation", f"{total_generation_mu:,.2f} MU")
KpiCard("💰 Total Revenue", f"₹{total_revenue_cr:,.2f} Cr")
KpiCard("💸 DSM Penalty", f"₹{total_penalty_cr:,.2f} Cr")
KpiCard("⚖️ Commercial Loss", f"{commercial_loss_pct:.2f}%")
KpiCard("🎯 Efficiency Score", f"{efficiency_score:.2f}")
```

---

## ✅ Final Verification

After deploying, verify all formulas:

- [ ] Generation: Sum(Column F) ÷ 10^6 = KPI value
- [ ] Revenue: Sum(Column I) ÷ 10^7 = KPI value
- [ ] Penalty: Sum(Column J) ÷ 10^7 = KPI value
- [ ] Loss %: (Penalty Cr / Revenue Cr) × 100 = KPI value
- [ ] Efficiency: 100 - Loss % = KPI value
- [ ] All KPIs update when filters change

**All formulas are now correctly implemented!** ✅
