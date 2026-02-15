import duckdb
import os

DB_PATH = "db/database.duckdb"


def init_database():
    """Create DuckDB database if not exists and initialize schema"""

    # Ensure db folder exists
    os.makedirs("db", exist_ok=True)

    con = duckdb.connect(DB_PATH)

    # ============================
    # Create Tables (idempotent)
    # ============================

    con.execute("""
    CREATE TABLE IF NOT EXISTS generation (
        id INTEGER,
        site_name TEXT,
        date DATE,
        generation_mwh DOUBLE
    );
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS dsm_penalty (
        id INTEGER,
        site_name TEXT,
        date DATE,
        penalty_rs DOUBLE
    );
    """)

    con.close()
