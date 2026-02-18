import os
import sqlite3
from functools import lru_cache


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "database", "nyc_taxi.db")

def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise Exception(f"Database connection failed: {str(e)}")

@lru_cache(maxsize=32)
def cached_query(query):
    try:
        conn = get_connection()
        rows = conn.execute(query).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        raise Exception(f"Database query error: {str(e)}")
