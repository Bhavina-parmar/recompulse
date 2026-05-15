from sentence_transformers import SentenceTransformer
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "recompulse.db"

model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, chunk_size=400):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)

    return chunks


def generate_chunks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM article_chunks")

    cursor.execute("SELECT id, content FROM items")
    articles = cursor.fetchall()

    print(f"🔄 Processing {len(articles)} articles...")

    for article_id, content in articles:
        chunks = chunk_text(content)

        for chunk in chunks:
            embedding = model.encode(chunk).tolist()

            cursor.execute(
                """
                INSERT INTO article_chunks (article_id, chunk_text, embedding)
                VALUES (?, ?, ?)
                """,
                (article_id, chunk, json.dumps(embedding))
            )

    conn.commit()
    conn.close()

    print("✅ All article chunks embedded and stored.")


if __name__ == "__main__":
    generate_chunks()