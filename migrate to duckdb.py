#!/usr/bin/env python3
"""
Migration Script: SQLite → DuckDB
Safely converts dsm_database.db (SQLite) to dsm_database.duckdb
"""

import sqlite3
import duckdb
import pandas as pd
import os
from datetime import datetime

SQLITE_PATH = "dsm_database.db"
DUCKDB_PATH = "dsm_database.duckdb"
BACKUP_PATH = f"dsm_database.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def migrate_sqlite_to_duckdb():
    """Main migration function"""
    
    print("=" * 60)
    print("SQLite → DuckDB Migration Script")
    print("=" * 60)
    
    # Check if SQLite DB exists
    if not os.path.exists(SQLITE_PATH):
        print(f"❌ SQLite database not found: {SQLITE_PATH}")
        print("ℹ️  Starting fresh with DuckDB...")
        initialize_fresh_duckdb()
        return
    
    # Backup SQLite DB
    print(f"\n📦 Creating backup: {BACKUP_PATH}")
    import shutil
    shutil.copy2(SQLITE_PATH, BACKUP_PATH)
    print("✅ Backup created")
    
    # Load data from SQLite
    print(f"\n📤 Loading data from SQLite...")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        df = pd.read_sql("SELECT * FROM dsm_data", sqlite_conn)
        sqlite_conn.close()
        
        print(f"✅ Loaded {len(df)} rows from SQLite")
        print(f"   Columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Failed to read SQLite: {str(e)}")
        return
    
    # Handle schema differences
    print(f"\n🔄 Normalizing schema...")
    df = normalize_schema(df)
    
    # Create DuckDB and insert data
    print(f"\n📥 Creating DuckDB database...")
    try:
        duckdb_conn = duckdb.connect(DUCKDB_PATH)
        
        # Create table
        duckdb_conn.execute("""
            CREATE TABLE IF NOT EXISTS dsm_data (
                Site VARCHAR,
                Connectivity VARCHAR,
                Technology VARCHAR,
                CY INTEGER,
                Month VARCHAR,
                Measured_Energy_kWh DOUBLE,
                Plant_Capacity DOUBLE,
                PPA_Rate DOUBLE,
                Actual_Revenue_INR DOUBLE,
                Total_Penalty_INR DOUBLE,
                Commercial_Loss DOUBLE,
                QCA VARCHAR,
                UNIQUE(Site, Month)
            )
        """)
        
        # Register dataframe
        duckdb_conn.register("migrated_data", df)
        
        # Insert data
        duckdb_conn.execute("""
            INSERT INTO dsm_data 
            SELECT * FROM migrated_data
        """)
        
        # Verify
        count = duckdb_conn.execute("SELECT COUNT(*) FROM dsm_data").fetchone()[0]
        duckdb_conn.close()
        
        print(f"✅ Inserted {count} rows into DuckDB")
        
    except Exception as e:
        print(f"❌ Failed to create DuckDB: {str(e)}")
        return
    
    # Success summary
    print("\n" + "=" * 60)
    print("✅ MIGRATION COMPLETE")
    print("=" * 60)
    print(f"SQLite backup: {BACKUP_PATH}")
    print(f"DuckDB created: {DUCKDB_PATH}")
    print(f"Rows migrated: {len(df)}")
    print("\n⚠️  Next steps:")
    print("1. Test the new DuckDB database")
    print("2. Once verified, you can delete the SQLite backup")
    print("3. Update your app to use db_manager.py (DuckDB version)")


def normalize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle schema differences between old SQLite and new DuckDB
    Maps old column names to canonical names
    """
    rename_map = {
        "Generation_kWh": "Measured_Energy_kWh",
        "Revenue_INR": "Actual_Revenue_INR",
        "DSM_Penalty_INR": "Total_Penalty_INR",
    }
    
    df = df.rename(columns=rename_map)
    
    # Ensure all canonical columns exist
    canonical_columns = [
        "Site", "Connectivity", "Technology", "CY", "Month",
        "Measured_Energy_kWh", "Plant_Capacity", "PPA_Rate",
        "Actual_Revenue_INR", "Total_Penalty_INR", "Commercial_Loss", "QCA"
    ]
    
    for col in canonical_columns:
        if col not in df.columns:
            df[col] = None
    
    # Return only canonical columns in correct order
    return df[canonical_columns]


def initialize_fresh_duckdb():
    """Initialize fresh DuckDB if no SQLite exists"""
    duckdb_conn = duckdb.connect(DUCKDB_PATH)
    
    duckdb_conn.execute("""
        CREATE TABLE IF NOT EXISTS dsm_data (
            Site VARCHAR,
            Connectivity VARCHAR,
            Technology VARCHAR,
            CY INTEGER,
            Month VARCHAR,
            Measured_Energy_kWh DOUBLE,
            Plant_Capacity DOUBLE,
            PPA_Rate DOUBLE,
            Actual_Revenue_INR DOUBLE,
            Total_Penalty_INR DOUBLE,
            Commercial_Loss DOUBLE,
            QCA VARCHAR,
            UNIQUE(Site, Month)
        )
    """)
    
    duckdb_conn.close()
    print(f"✅ Fresh DuckDB database created: {DUCKDB_PATH}")


if __name__ == "__main__":
    migrate_sqlite_to_duckdb()