import json
from pathlib import Path
from collections import Counter
from app.db import EVENTS
from app.db import IMPRESSIONS

DATA_PATH = Path("../data/items.json")

def load_items():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_user_preferred_categories(user_id: int):
    user_events = [
        e for e in EVENTS
        if e["user_id"] == user_id and e["action"] == "click"
    ]

    if not user_events:
        return []

    clicked_item_ids = [e["item_id"] for e in user_events]
    items = load_items()

    clicked_categories = [
        item["category"]
        for item in items
        if item["id"] in clicked_item_ids
    ]

    return [cat for cat, _ in Counter(clicked_categories).most_common()]



def recommend_for_user(user_id: int):
    items = load_items()
    preferred_categories = get_user_preferred_categories(user_id)

    if preferred_categories:
        preferred = [i for i in items if i["category"] in preferred_categories]
        others = [i for i in items if i["category"] not in preferred_categories]
        items = preferred + others

    # ✅ Track impressions
    for item in items:
        item_id = item["id"]
        IMPRESSIONS[item_id] = IMPRESSIONS.get(item_id, 0) + 1

    return items

