from sentence_transformers import SentenceTransformer
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "recompulse.db"

model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embeddings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM items")
    rows = cursor.fetchall()

    print(f"🔄 Generating embeddings for {len(rows)} articles...")

    for item_id, title, content in rows:
        text = f"{title}. {content}"
        embedding = model.encode(text).tolist()

        cursor.execute(
            "UPDATE items SET embedding = ? WHERE id = ?",
            (json.dumps(embedding), item_id)
        )

    conn.commit()
    conn.close()

    print("✅ All embeddings stored successfully.")

if __name__ == "__main__":
    generate_embeddings()