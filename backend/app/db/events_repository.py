import sqlite3
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "backend" / "recompulse.db"

def log_event(user_id: int, item_id: int, action: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (user_id, item_id, action, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, item_id, action, int(time.time())))

    conn.commit()
    conn.close()


def get_all_events():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, item_id, action, timestamp
        FROM events
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "user_id": r[0],
            "item_id": r[1],
            "action": r[2],
            "timestamp": r[3]
        }
        for r in rows
    ]