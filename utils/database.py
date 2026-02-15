import sqlite3
import pandas as pd

DB_PATH = "dsm_database.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dsm_data (
        Site TEXT,
        Connectivity TEXT,
        Technology TEXT,
        CY INTEGER,
        Month TEXT,
        Generation_kWh REAL,
        Plant_Capacity REAL,
        PPA_Rate REAL,
        Revenue_INR REAL,
        DSM_Penalty_INR REAL,
        Commercial_Loss REAL,
        QCA TEXT,
        UNIQUE(Site, Month)
    )
    """)

    conn.commit()
    conn.close()


def insert_data(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("dsm_data", conn, if_exists="append", index=False)
    conn.close()


def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM dsm_data", conn)
    conn.close()
    return df
