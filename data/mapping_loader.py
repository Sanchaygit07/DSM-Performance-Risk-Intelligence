# data/mapping_loader.py
import pandas as pd
import os

MAPPING_FILE = "data/site_mapping.csv"

def load_site_mapping():
    """Load site mapping data from CSV"""
    if os.path.exists(MAPPING_FILE):
        return pd.read_csv(MAPPING_FILE)
    else:
        # Return empty DataFrame with expected columns if file doesn't exist
        return pd.DataFrame(columns=[
            'Site', 'Connectivity', 'Plant_AC_Capacity', 'PPA_Rate',
            'Technology', 'QCA', 'Power_Sale_Category', 'State', 
            'State_Code', 'Site_Name'
        ])


def enrich_dsm_data(df):
    """
    Enrich DSM data with site mapping information
    Only adds columns that don't exist in raw data - preserves raw data values
    
    Args:
        df: DataFrame with DSM data (must have 'Site' column)
    
    Returns:
        DataFrame with added columns: Connectivity, Technology, QCA, 
        Power_Sale_Category, State, State_Code, Site_Name
    """
    mapping_df = load_site_mapping()
    
    if mapping_df.empty or 'Site' not in df.columns:
        return df
    
    # Determine which columns to add from mapping (only if not in raw data)
    mapping_columns = ['Connectivity', 'Plant_AC_Capacity', 'PPA_Rate', 
                      'Technology', 'QCA', 'Power_Sale_Category', 
                      'State', 'State_Code', 'Site_Name']
    
    # Only select columns from mapping that don't exist in raw data
    columns_to_add = ['Site']  # Always need Site for merge
    for col in mapping_columns:
        if col in mapping_df.columns and col not in df.columns:
            columns_to_add.append(col)
    
    # If no columns to add, return original
    if len(columns_to_add) == 1:  # Only 'Site'
        return df
    
    # Select only needed columns from mapping
    mapping_subset = mapping_df[columns_to_add].drop_duplicates(subset=['Site'])
    
    # Merge on Site column (left join preserves all raw data)
    enriched = df.merge(
        mapping_subset,
        on='Site',
        how='left'
    )
    
    return enriched
