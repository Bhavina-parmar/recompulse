import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "backend" / "recompulse.db"
ITEMS_JSON_PATH = BASE_DIR / "data" / "items.json"

def seed_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(ITEMS_JSON_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        cursor.execute("""
            INSERT OR IGNORE INTO items (id, title, category, content, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            item["id"],
            item["title"],
            item["category"],
            item.get("content", ""),
            item["created_at"]
        ))

    conn.commit()
    conn.close()

    print("Items seeded successfully.")