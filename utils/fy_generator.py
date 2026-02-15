# utils/fy_generator.py

import pandas as pd


def generate_financial_year(date_series):
    """
    Generate Financial Year (Apr-Mar)
    Example:
    Apr 2025 -> FY2026
    Jan 2026 -> FY2026
    """
    fy = date_series.apply(
        lambda x: f"FY{x.year + 1}" if x.month >= 4 else f"FY{x.year}"
    )
    return fy


def generate_financial_quarter(date_series):
    """
    Q1 -> Apr-Jun
    Q2 -> Jul-Sep
    Q3 -> Oct-Dec
    Q4 -> Jan-Mar
    """
    def get_quarter(month):
        if month in [4, 5, 6]:
            return "Q1"
        elif month in [7, 8, 9]:
            return "Q2"
        elif month in [10, 11, 12]:
            return "Q3"
        else:
            return "Q4"

    return date_series.dt.month.apply(get_quarter)
