import duckdb

DB_PATH = "db/database.duckdb"

def get_connection():
    return duckdb.connect(DB_PATH)
