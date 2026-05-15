import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "recompulse.db"

model = SentenceTransformer("all-MiniLM-L6-v2")


def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def retrieve_semantic_candidates(user_query=None, top_k=30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, category, content, embedding, created_at FROM items")
    rows = cursor.fetchall()

    if user_query is None:
        # fallback → use all
        return [
            {
                "id": r[0],
                "title": r[1],
                "category": r[2],
                "content": r[3],
                "created_at": r[5]
            }
            for r in rows
        ]

    query_embedding = model.encode(user_query)

    scored = []

    for r in rows:
        item_embedding = json.loads(r[4])
        sim = cosine_similarity(query_embedding, item_embedding)

        scored.append((sim, r))

    scored.sort(reverse=True, key=lambda x: x[0])

    top_items = []

    for _, r in scored[:top_k]:
        top_items.append({
            "id": r[0],
            "title": r[1],
            "category": r[2],
            "content": r[3],
            "created_at": r[5]
        })

    conn.close()

    return top_items

def build_user_profile_embedding(user_id, limit=3):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # get last N clicked items
    cursor.execute("""
        SELECT i.title, i.content
        FROM events e
        JOIN items i ON e.item_id = i.id
        WHERE e.user_id = ?
        AND e.action = 'click'
        ORDER BY e.timestamp DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    combined_text = " ".join([f"{r[0]}. {r[1]}" for r in rows])

    return model.encode(combined_text)

def retrieve_candidates_for_user(user_id, top_k=30):
    user_embedding = build_user_profile_embedding(user_id)

    if user_embedding is None:
        # cold start → return all items
        return retrieve_semantic_candidates(None)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, category, content, embedding, created_at FROM items")
    rows = cursor.fetchall()

    scored = []

    for r in rows:
        item_embedding = json.loads(r[4])
        sim = cosine_similarity(user_embedding, item_embedding)

        scored.append((sim, r))

    scored.sort(reverse=True, key=lambda x: x[0])

    top_items = []

    for _, r in scored[:top_k]:
        top_items.append({
            "id": r[0],
            "title": r[1],
            "category": r[2],
            "content": r[3],
            "created_at": r[5]
        })

    conn.close()

    return top_items