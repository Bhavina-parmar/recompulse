import json
from pathlib import Path

DATA_PATH = Path("../data/items.json")

def load_items():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def recommend_for_user(user_id: int):
    # Day-2 logic: return all items
    # Personalization comes later
    return load_items()
