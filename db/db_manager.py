import duckdb
import pandas as pd
from typing import Tuple, Dict
from datetime import datetime

DB_PATH = "dsm_database.duckdb"

# ===============================
# CANONICAL SCHEMA DEFINITION
# ===============================
SCHEMA_DEFINITION = {
    "Site": "VARCHAR",
    "Connectivity": "VARCHAR",
    "Technology": "VARCHAR",
    "CY": "INTEGER",
    "Month": "VARCHAR",
    "Measured_Energy_kWh": "DOUBLE",
    "Plant_Capacity": "DOUBLE",
    "PPA_Rate": "DOUBLE",
    "Actual_Revenue_INR": "DOUBLE",
    "Total_Penalty_INR": "DOUBLE",
    "Commercial_Loss": "DOUBLE",
    "QCA": "VARCHAR",
}

REQUIRED_COLUMNS = [
    "Site",
    "Month",
    "Measured_Energy_kWh",
    "Actual_Revenue_INR",
    "Total_Penalty_INR",
    "QCA"
]

UNIQUE_KEY = ["Site", "Month"]


# ===============================
# DATABASE CONNECTION
# ===============================
def get_connection():
    """Get DuckDB connection with optimal settings"""
    con = duckdb.connect(DB_PATH)
    # Enable progress bars for large queries (optional)
    con.execute("SET enable_progress_bar=false")
    return con


# ===============================
# INITIALIZE DATABASE
# ===============================
def initialize_database():
    """Create table with explicit schema"""
    con = get_connection()
    
    # Build CREATE TABLE statement from schema definition
    columns_def = ", ".join([f"{col} {dtype}" for col, dtype in SCHEMA_DEFINITION.items()])
    unique_constraint = f"UNIQUE({', '.join(UNIQUE_KEY)})"
    
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS dsm_data (
            {columns_def},
            {unique_constraint}
        )
    """)
    
    # Create ingestion logs table
    con.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_logs (
            log_id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP,
            filename VARCHAR,
            rows_inserted INTEGER,
            rows_updated INTEGER,
            rows_skipped INTEGER,
            status VARCHAR,
            error_message VARCHAR
        )
    """)
    
    # Create sequence for log_id
    con.execute("""
        CREATE SEQUENCE IF NOT EXISTS log_id_seq START 1
    """)
    
    con.close()


# ===============================
# VALIDATE DATAFRAME SCHEMA
# ===============================
def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate dataframe against canonical schema
    Returns: (is_valid, error_message)
    """
    # Check required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}"
    
    # Check for null values in unique key columns
    for col in UNIQUE_KEY:
        if df[col].isnull().any():
            null_count = df[col].isnull().sum()
            return False, f"Column '{col}' contains {null_count} null values (unique key cannot be null)"
    
    # Check for internal duplicates in upload
    duplicates = df.duplicated(subset=UNIQUE_KEY, keep=False)
    if duplicates.any():
        dup_count = duplicates.sum()
        return False, f"Upload contains {dup_count} duplicate rows (based on Site + Month)"
    
    # Validate numeric columns can be cast
    numeric_cols = {col: dtype for col, dtype in SCHEMA_DEFINITION.items() 
                    if dtype == "DOUBLE" and col in df.columns}
    
    for col in numeric_cols:
        try:
            pd.to_numeric(df[col], errors='coerce')
        except Exception as e:
            return False, f"Column '{col}' contains non-numeric data: {str(e)}"
    
    return True, ""


# ===============================
# DETECT DUPLICATES
# ===============================
def detect_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect which rows already exist in database
    Returns: (existing_rows_df, new_rows_df)
    """
    con = get_connection()
    
    # Get existing (Site, Month) combinations
    existing_keys = con.execute(f"""
        SELECT {', '.join(UNIQUE_KEY)}
        FROM dsm_data
    """).fetchdf()
    
    con.close()
    
    if existing_keys.empty:
        return pd.DataFrame(), df
    
    # Create merge key for comparison
    df['_merge_key'] = df[UNIQUE_KEY].astype(str).agg('||'.join, axis=1)
    existing_keys['_merge_key'] = existing_keys[UNIQUE_KEY].astype(str).agg('||'.join, axis=1)
    
    # Split into existing vs new
    existing_mask = df['_merge_key'].isin(existing_keys['_merge_key'])
    
    existing_rows = df[existing_mask].drop('_merge_key', axis=1).copy()
    new_rows = df[~existing_mask].drop('_merge_key', axis=1).copy()
    
    return existing_rows, new_rows


# ===============================
# ALIGN DATAFRAME TO SCHEMA
# ===============================
def align_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure dataframe matches canonical schema exactly
    - Orders columns correctly
    - Adds missing optional columns with NULL
    - Drops extra columns
    - Casts types
    """
    aligned = pd.DataFrame()
    
    for col, dtype in SCHEMA_DEFINITION.items():
        if col in df.columns:
            # Column exists - cast to correct type
            if dtype == "DOUBLE":
                aligned[col] = pd.to_numeric(df[col], errors='coerce')
            elif dtype == "INTEGER":
                aligned[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            else:  # VARCHAR
                aligned[col] = df[col].astype(str).replace('nan', None)
        else:
            # Column missing - add as NULL
            aligned[col] = None
    
    return aligned


# ===============================
# INSERT DATA (UPSERT LOGIC)
# ===============================
def insert_dsm_data(
    df: pd.DataFrame, 
    overwrite_duplicates: bool = True,
    filename: str = "unknown"
) -> Dict[str, int]:
    """
    Insert data into DuckDB with smart upsert logic
    
    Args:
        df: DataFrame with standardized columns
        overwrite_duplicates: If True, replace existing rows. If False, skip them.
        filename: Source filename for logging
    
    Returns:
        Dict with insertion statistics
    """
    con = get_connection()
    stats = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "total": len(df)
    }
    
    try:
        # Validate before proceeding
        is_valid, error_msg = validate_dataframe(df)
        if not is_valid:
            log_ingestion(con, filename, 0, 0, len(df), "FAILED", error_msg)
            raise ValueError(f"Validation failed: {error_msg}")
        
        # Align to schema
        df_aligned = align_to_schema(df)
        
        # Detect duplicates
        existing_rows, new_rows = detect_duplicates(df_aligned)
        
        if overwrite_duplicates and not existing_rows.empty:
            # MERGE strategy: Delete existing then insert all
            # Register dataframe as virtual table
            con.register("upload_data", df_aligned)
            
            # Delete existing records
            con.execute(f"""
                DELETE FROM dsm_data
                WHERE ({', '.join(UNIQUE_KEY)}) IN (
                    SELECT {', '.join(UNIQUE_KEY)}
                    FROM upload_data
                )
            """)
            
            # Insert all rows
            columns = list(SCHEMA_DEFINITION.keys())
            columns_str = ', '.join(columns)
            
            con.execute(f"""
                INSERT INTO dsm_data ({columns_str})
                SELECT {columns_str}
                FROM upload_data
            """)
            
            stats["updated"] = len(existing_rows)
            stats["inserted"] = len(new_rows)
            
        else:
            # Insert only new rows (skip duplicates)
            if new_rows.empty:
                stats["skipped"] = len(df)
            else:
                con.register("new_data", new_rows)
                columns = list(SCHEMA_DEFINITION.keys())
                columns_str = ', '.join(columns)
                
                con.execute(f"""
                    INSERT INTO dsm_data ({columns_str})
                    SELECT {columns_str}
                    FROM new_data
                """)
                
                stats["inserted"] = len(new_rows)
                stats["skipped"] = len(existing_rows)
        
        # Log successful ingestion
        log_ingestion(
            con, filename, 
            stats["inserted"], 
            stats["updated"], 
            stats["skipped"], 
            "SUCCESS", 
            None
        )
        
    except Exception as e:
        log_ingestion(con, filename, 0, 0, len(df), "FAILED", str(e))
        raise
    
    finally:
        con.close()
    
    return stats


# ===============================
# FETCH DATA
# ===============================
def fetch_dsm_data() -> pd.DataFrame:
    """Fetch all data from database"""
    con = get_connection()
    df = con.execute("SELECT * FROM dsm_data").fetchdf()
    con.close()
    return df


# ===============================
# CHECK DATA EXISTS
# ===============================
def has_data() -> bool:
    """Check if database contains any data"""
    con = get_connection()
    count = con.execute("SELECT COUNT(*) FROM dsm_data").fetchone()[0]
    con.close()
    return count > 0


# ===============================
# INGESTION LOGGING
# ===============================
def log_ingestion(
    con, 
    filename: str, 
    inserted: int, 
    updated: int, 
    skipped: int, 
    status: str, 
    error: str = None
):
    """Log ingestion event to database"""
    con.execute("""
        INSERT INTO ingestion_logs 
        (log_id, timestamp, filename, rows_inserted, rows_updated, rows_skipped, status, error_message)
        VALUES (
            nextval('log_id_seq'),
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
    """, [datetime.now(), filename, inserted, updated, skipped, status, error])


# ===============================
# GET INGESTION LOGS
# ===============================
def get_ingestion_logs(limit: int = 10) -> pd.DataFrame:
    """Fetch recent ingestion logs"""
    con = get_connection()
    df = con.execute(f"""
        SELECT * FROM ingestion_logs 
        ORDER BY timestamp DESC 
        LIMIT {limit}
    """).fetchdf()
    con.close()
    return df


# ===============================
# DIAGNOSTICS: PREVIEW SCHEMA MAPPING
# ===============================
def preview_schema_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Show how uploaded columns map to canonical schema
    Returns diagnostic dataframe
    """
    mapping = []
    
    for canon_col, dtype in SCHEMA_DEFINITION.items():
        exists = "✅" if canon_col in df.columns else "❌"
        sample = df[canon_col].iloc[0] if canon_col in df.columns and not df.empty else None
        required = "⚠️ REQUIRED" if canon_col in REQUIRED_COLUMNS else ""
        
        mapping.append({
            "Canonical Column": canon_col,
            "Type": dtype,
            "Present": exists,
            "Sample Value": sample,
            "Status": required
        })
    
    return pd.DataFrame(mapping)
