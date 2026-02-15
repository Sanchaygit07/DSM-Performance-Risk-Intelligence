import pandas as pd
import re
from typing import Dict, List

# ===============================
# NORMALIZATION FUNCTION
# ===============================
def normalize(col: str) -> str:
    """
    Aggressive normalization to handle dirty headers
    - Lowercase
    - Remove spaces, parentheses, %, special chars
    - Strip whitespace
    """
    return (
        str(col)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "")
        .replace("_", "")
        .replace("-", "")
        .replace(".", "")
    )


# ===============================
# MASTER COLUMN MAPPING DICTIONARY
# ===============================
# Maps: normalized_input_column -> canonical_column
COLUMN_MAP = {
    # Site variations
    "site": "Site",
    "sitename": "Site",
    "location": "Site",
    "plant": "Site",
    
    # Connectivity
    "connectivity": "Connectivity",
    "connection": "Connectivity",
    "gridconnection": "Connectivity",
    
    # Technology
    "technology": "Technology",
    "tech": "Technology",
    "type": "Technology",
    "planttype": "Technology",
    
    # Calendar Year
    "cy": "CY",
    "calendaryear": "CY",
    "year": "CY",
    
    # Month
    "month": "Month",
    "monthyear": "Month",
    "period": "Month",
    "date": "Month",
    
    # Energy/Generation
    "measuredenergykwh": "Measured_Energy_kWh",
    "generationkwh": "Measured_Energy_kWh",
    "energykwh": "Measured_Energy_kWh",
    "generation": "Measured_Energy_kWh",
    "energygeneration": "Measured_Energy_kWh",
    "kwh": "Measured_Energy_kWh",
    
    # Plant Capacity
    "plantcapacity": "Plant_Capacity",
    "plantrcapacity": "Plant_Capacity",
    "capacity": "Plant_Capacity",
    "installedcapacity": "Plant_Capacity",
    "plantcapacitymw": "Plant_Capacity",
    
    # PPA Rate
    "pparate": "PPA_Rate",
    "rate": "PPA_Rate",
    "tariff": "PPA_Rate",
    "ppatariff": "PPA_Rate",
    
    # Revenue
    "actualrevenueinr": "Actual_Revenue_INR",
    "revenueinr": "Actual_Revenue_INR",
    "revenue": "Actual_Revenue_INR",
    "actualrevenue": "Actual_Revenue_INR",
    "totalrevenue": "Actual_Revenue_INR",
    
    # Penalty
    "totalpenaltyinr": "Total_Penalty_INR",
    "dsmpenaltyinr": "Total_Penalty_INR",
    "penalty": "Total_Penalty_INR",
    "dsmpenalty": "Total_Penalty_INR",
    "penaltyinr": "Total_Penalty_INR",
    
    # Commercial Loss
    "commercialloss": "Commercial_Loss",
    "commercialloss%": "Commercial_Loss",
    "loss": "Commercial_Loss",
    "loss%": "Commercial_Loss",
    "losspercent": "Commercial_Loss",
    "closs": "Commercial_Loss",
    
    # QCA
    "qca": "QCA",
    "buyer": "QCA",
    "customer": "QCA",
    "offtaker": "QCA",
}


# ===============================
# SITE CLEANING RULES
# ===============================
SITE_ALIASES = {
    "washi1": "WASHI",
    "washi2": "WASHI",
    "washi 1": "WASHI",
    "washi 2": "WASHI",
    "tx 12": "TX_12",
    "tx12": "TX_12",
    "tx-12": "TX_12",
    "bheemshakti": "BHEEMSHAKTI",
    "bheem shakti": "BHEEMSHAKTI",
}


# ===============================
# QCA CLEANING RULES
# ===============================
QCA_ALIASES = {
    # All lowercase keys for matching
    "cliamte connect": "Climate Connect",      # Fix typo
    "climate connect": "Climate Connect",
    "climateconnect": "Climate Connect",
    "reconnect": "Reconnect",
    "re connect": "Reconnect",
    "re-connect": "Reconnect",
    "manikaran": "Manikaran",
    "unilink": "Unilink",
    "uni link": "Unilink",
    "uni-link": "Unilink",
}


# ===============================
# STANDARDIZE COLUMNS
# ===============================
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main function to standardize uploaded dataframe
    
    Steps:
    1. Normalize column names
    2. Map to canonical schema
    3. Clean Site values
    4. Clean QCA values
    5. Handle Month formatting
    
    Returns: DataFrame with canonical column names
    """
    df = df.copy()
    
    # -------------------------
    # STEP 1: BUILD RENAME MAP
    # -------------------------
    rename_map = {}
    unmatched_columns = []
    
    for original_col in df.columns:
        normalized = normalize(original_col)
        
        if normalized in COLUMN_MAP:
            canonical = COLUMN_MAP[normalized]
            rename_map[original_col] = canonical
        else:
            unmatched_columns.append(original_col)
    
    # Apply renaming
    df = df.rename(columns=rename_map)
    
    # Log unmatched columns (optional - can be shown in diagnostics)
    if unmatched_columns:
        print(f"⚠️ Unmatched columns (will be ignored): {unmatched_columns}")
    
    # -------------------------
    # STEP 2: CLEAN SITE VALUES
    # -------------------------
    if "Site" in df.columns:
        df["Site"] = (
            df["Site"]
            .astype(str)
            .str.strip()
            .str.lower()
            .replace(SITE_ALIASES)
            .str.upper()
            .replace("NAN", None)
        )
    
    # -------------------------
    # STEP 3: CLEAN QCA VALUES
    # -------------------------
    if "QCA" in df.columns:
        # Clean QCA values properly
        def clean_qca(val):
            if pd.isna(val) or str(val).strip() == '' or str(val).lower() == 'nan':
                return None
            # Strip spaces and convert to lowercase
            cleaned = str(val).strip().lower()
            # Check aliases
            if cleaned in QCA_ALIASES:
                return QCA_ALIASES[cleaned]
            # Title case the result
            return val.strip().title()
        
        df["QCA"] = df["QCA"].apply(clean_qca)
    
    # -------------------------
    # STEP 4: STANDARDIZE MONTH FORMAT
    # -------------------------
    if "Month" in df.columns:
        df["Month"] = standardize_month(df["Month"])
    
    # -------------------------
    # STEP 5: ENSURE NUMERIC TYPES
    # -------------------------
    numeric_columns = [
        "Measured_Energy_kWh",
        "Plant_Capacity",
        "PPA_Rate",
        "Actual_Revenue_INR",
        "Total_Penalty_INR",
        "Commercial_Loss",
        "CY"
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


# ===============================
# MONTH STANDARDIZATION
# ===============================
def standardize_month(month_series: pd.Series) -> pd.Series:
    """
    Convert various month formats to standardized 'YYYY-MM-DD' format
    
    Handles:
    - "Jan-25", "January 2025"
    - "01/2025", "2025-01"
    - Excel serial dates
    - Already formatted dates
    """
    def parse_month(val):
        if pd.isna(val):
            return None
        
        val_str = str(val).strip()
        
        # Try pandas auto-parse first
        try:
            parsed = pd.to_datetime(val_str, errors='coerce')
            if pd.notna(parsed):
                # Return first day of month
                return parsed.strftime('%Y-%m-01')
        except:
            pass
        
        # Handle "Jan-25" format
        if "-" in val_str and len(val_str) <= 7:
            try:
                parts = val_str.split("-")
                if len(parts) == 2:
                    month_abbr = parts[0]
                    year = parts[1]
                    
                    # Expand 2-digit year
                    if len(year) == 2:
                        year = "20" + year if int(year) < 50 else "19" + year
                    
                    parsed = pd.to_datetime(f"{month_abbr} {year}", format='%b %Y')
                    return parsed.strftime('%Y-%m-01')
            except:
                pass
        
        return None
    
    return month_series.apply(parse_month)


# ===============================
# VALIDATION HELPERS
# ===============================
def get_mapping_report(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Generate diagnostic report showing column mapping results
    Returns dict with matched, unmatched, and missing columns
    """
    normalized_input = {normalize(col): col for col in df.columns}
    expected_canonical = set(COLUMN_MAP.values())
    
    matched = []
    unmatched = []
    missing = []
    
    # Check what matched
    for norm_col, orig_col in normalized_input.items():
        if norm_col in COLUMN_MAP:
            matched.append(f"{orig_col} → {COLUMN_MAP[norm_col]}")
        else:
            unmatched.append(orig_col)
    
    # Check what's missing
    mapped_canonical = set(COLUMN_MAP[norm] for norm in normalized_input.keys() if norm in COLUMN_MAP)
    missing = list(expected_canonical - mapped_canonical)
    
    return {
        "matched": matched,
        "unmatched": unmatched,
        "missing": missing
    }


# ===============================
# FUZZY COLUMN MATCHING (BONUS)
# ===============================
def suggest_column_matches(df: pd.DataFrame) -> Dict[str, str]:
    """
    For unmatched columns, suggest potential canonical matches
    Uses basic string similarity
    """
    from difflib import get_close_matches
    
    suggestions = {}
    canonical_names = list(set(COLUMN_MAP.values()))
    
    for col in df.columns:
        normalized = normalize(col)
        if normalized not in COLUMN_MAP:
            # Find closest match
            matches = get_close_matches(normalized, 
                                       [normalize(c) for c in canonical_names], 
                                       n=1, 
                                       cutoff=0.6)
            if matches:
                # Map back to canonical name
                for canon in canonical_names:
                    if normalize(canon) == matches[0]:
                        suggestions[col] = canon
                        break
    
    return suggestions
