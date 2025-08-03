import sqlite3
from datetime import datetime
import json

DB_NAME = "claim_log.db"

def setup_database():
    """Create the database and the 'logs' table with the new schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            document_links TEXT,
            user_query TEXT NOT NULL,
            llm_response TEXT,
            time_taken_sec REAL,
            model_used TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_request(doc_links, query, response_text, time_taken, model_name):
    """Log the request details, including document links, to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Convert list of links to a JSON string for storage
    links_json = json.dumps(doc_links) if doc_links else None
    
    cursor.execute("""
        INSERT INTO logs (timestamp, document_links, user_query, llm_response, time_taken_sec, model_used)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(),
        links_json,
        query,
        response_text,
        time_taken,
        model_name
    ))
    conn.commit()
    conn.close()