import sqlite3
from pathlib import Path

from app.database import get_connection 

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "backend" / "recompulse.db"

def get_all_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, category, content, created_at FROM items")
    rows = cursor.fetchall()

    conn.close()

    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "title": row[1],
            "category": row[2],
            "content": row[3],
            "created_at": row[4]
        })

    return items

def get_item_by_id(item_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, category, content, created_at FROM items WHERE id = ?",
        (item_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "category": row[2],
        "content": row[3],
        "created_at": row[4]
    }