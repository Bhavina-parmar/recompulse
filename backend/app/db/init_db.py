import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "recompulse.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            content TEXT,
            created_at INTEGER NOT NULL
        )
    """)

    # Create article_chunks table for RAG
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            FOREIGN KEY (article_id) REFERENCES items (id)
        )
    """)

    # Create events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()