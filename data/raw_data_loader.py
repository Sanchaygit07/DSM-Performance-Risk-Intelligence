# data/raw_data_loader.py

import pandas as pd
from io import BytesIO


def load_uploaded_file(uploaded_file):

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    else:
        file_bytes = BytesIO(uploaded_file.read())
        xls = pd.ExcelFile(file_bytes)

        # Prefer raw Data sheet
        if "raw Data" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="raw Data")
        else:
            df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

    return df
