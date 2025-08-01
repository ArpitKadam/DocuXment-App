import sqlite3
from datetime import datetime

DB_NAME = "claims_log.db"

def setup_database():
    """Create the database and the 'claims' table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            user_query TEXT NOT NULL,
            llm_decision TEXT,
            llm_amount TEXT,
            llm_justification TEXT,
            model_used TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_claim(query, result_obj, model_name):
    """Log the user's query and the parsed result to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO claims (timestamp, user_query, llm_decision, llm_amount, llm_justification, model_used)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(),
        query,
        result_obj.Decision,
        result_obj.Amount,
        result_obj.Justification,
        model_name
    ))
    conn.commit()
    conn.close()