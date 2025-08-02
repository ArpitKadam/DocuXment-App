import sqlite3
from datetime import datetime

DB_NAME = "claims_log.db"

def setup_database():
    """Create the database and the 'logs' table with the new schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # KEY CHANGE: Updated table columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            user_query TEXT NOT NULL,
            llm_response TEXT,
            time_taken_sec REAL,
            model_used TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_request(query, response_text, time_taken, model_name):
    """Log the request details to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # KEY CHANGE: Updated INSERT statement to match the new schema
    cursor.execute("""
        INSERT INTO logs (timestamp, user_query, llm_response, time_taken_sec, model_used)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now(),
        query,
        response_text,
        time_taken,
        model_name
    ))
    conn.commit()
    conn.close()