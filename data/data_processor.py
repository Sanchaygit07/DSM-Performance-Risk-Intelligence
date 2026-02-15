# data/data_processor.py

import pandas as pd
from utils.fy_generator import generate_financial_year, generate_financial_quarter
from data.mapping_loader import load_site_mapping


def process_data(df, existing_df=None):

    # Clean column names
    df.columns = df.columns.str.strip()

    # ------------------------
    # Flexible Column Mapping
    # ------------------------
    column_map = {}

    for col in df.columns:
        col_clean = col.strip().lower()

        if "measured" in col_clean and "kwh" in col_clean:
            column_map[col] = "Generation_kWh"

        elif "actual" in col_clean and "revenue" in col_clean:
            column_map[col] = "Revenue_INR"

        elif "penalty" in col_clean:
            column_map[col] = "DSM_Penalty_INR"

        elif col_clean == "site":
            column_map[col] = "Site"

        elif col_clean == "month":
            column_map[col] = "Month"

        elif col_clean == "connectivity":
            column_map[col] = "Connectivity"

        elif col_clean == "qca":
            column_map[col] = "QCA"

    df.rename(columns=column_map, inplace=True)

    # Convert Month to datetime
    df["Month"] = pd.to_datetime(df["Month"])

    # Merge mapping
    mapping_df = load_site_mapping()
    df = df.merge(mapping_df, on="Site", how="left")

    # Generate FY & Quarter
    df["FY"] = generate_financial_year(df["Month"])
    df["Quarter"] = generate_financial_quarter(df["Month"])

    # Commercial Loss %
    df["Commercial_Loss_%"] = (
        df["DSM_Penalty_INR"] / df["Revenue_INR"]
    ) * 100

    # Efficiency Score
    df["Efficiency_Score"] = 100 - df["Commercial_Loss_%"]

    # Unique Key
    df["Unique_Key"] = (
        df["Site"] +
        df["Month"].astype(str) +
        df["FY"]
    )

    duplicates = pd.DataFrame()

    if existing_df is not None and not existing_df.empty:
        duplicate_mask = df["Unique_Key"].isin(existing_df["Unique_Key"])
        duplicates = df[duplicate_mask]
        df = df[~duplicate_mask]

    return df, duplicates
