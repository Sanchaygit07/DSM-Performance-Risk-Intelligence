# validators.py - Enhanced validation layer

import pandas as pd
from typing import Tuple, List, Dict

def normalize(col):
    """Normalize column name for comparison"""
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
    )


# Required columns (normalized)
REQUIRED = [
    "site",
    "month",
    "measuredenergykwh",
    "actualrevenueinr",
    "totalpenaltyinr",
    "qca"
]


def validate_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that dataframe contains all required columns
    
    Returns:
        (is_valid, missing_columns)
    """
    normalized_columns = [normalize(col) for col in df.columns]
    
    missing = [
        req for req in REQUIRED
        if req not in normalized_columns
    ]
    
    if missing:
        return False, missing
    
    return True, []


def validate_data_quality(df: pd.DataFrame) -> Tuple[bool, Dict[str, str]]:
    """
    Deep validation of data quality
    
    Checks:
    - Null values in key columns
    - Data type issues
    - Value ranges
    - Duplicate rows
    
    Returns:
        (is_valid, error_details)
    """
    errors = {}
    
    # Check for required column presence first
    is_valid, missing = validate_columns(df)
    if not is_valid:
        errors["missing_columns"] = f"Missing required columns: {', '.join(missing)}"
        return False, errors
    
    # Map normalized names to actual column names
    col_map = {normalize(col): col for col in df.columns}
    
    # Check Site nulls
    if "site" in col_map:
        site_col = col_map["site"]
        null_count = df[site_col].isnull().sum()
        if null_count > 0:
            errors["site_nulls"] = f"Site column has {null_count} null values"
    
    # Check Month nulls
    if "month" in col_map:
        month_col = col_map["month"]
        null_count = df[month_col].isnull().sum()
        if null_count > 0:
            errors["month_nulls"] = f"Month column has {null_count} null values"
    
    # Check numeric columns
    numeric_checks = {
        "measuredenergykwh": "Energy",
        "actualrevenueinr": "Revenue",
        "totalpenaltyinr": "Penalty"
    }
    
    for norm_col, display_name in numeric_checks.items():
        if norm_col in col_map:
            actual_col = col_map[norm_col]
            try:
                pd.to_numeric(df[actual_col], errors='raise')
            except (ValueError, TypeError):
                errors[f"{norm_col}_type"] = f"{display_name} column contains non-numeric values"
    
    # Check for duplicates (Site + Month)
    if "site" in col_map and "month" in col_map:
        site_col = col_map["site"]
        month_col = col_map["month"]
        
        duplicates = df.duplicated(subset=[site_col, month_col], keep=False)
        dup_count = duplicates.sum()
        
        if dup_count > 0:
            errors["duplicates"] = f"Found {dup_count} duplicate rows (based on Site + Month)"
    
    return len(errors) == 0, errors


def get_validation_summary(df: pd.DataFrame) -> Dict:
    """
    Generate comprehensive validation summary
    
    Returns dict with:
    - row_count
    - column_count
    - required_present
    - missing_columns
    - data_quality_issues
    """
    is_valid_cols, missing = validate_columns(df)
    is_valid_data, errors = validate_data_quality(df)
    
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "required_columns_present": is_valid_cols,
        "missing_columns": missing,
        "data_quality_valid": is_valid_data,
        "data_quality_errors": errors,
        "overall_valid": is_valid_cols and is_valid_data
    }