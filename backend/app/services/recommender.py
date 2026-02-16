import json
import joblib
from pathlib import Path
from collections import Counter
from app.db import EVENTS
#from app.db import IMPRESSIONS
from app.db import CLICKS, IMPRESSIONS
import pandas as pd
import os

MODEL_PATH = Path("model.pkl")


try:
    model, feature_columns = joblib.load(MODEL_PATH)
    print("✅ MODEL LOADED SUCCESSFULLY")
except Exception as e:
    print("❌ MODEL LOAD FAILED:", e)
    model = None
    feature_columns = []



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


def get_item_ctr(item_id: int):
    impressions = IMPRESSIONS.get(item_id, 0)
    clicks = CLICKS.get(item_id, 0)
    return clicks / impressions if impressions > 0 else 0
def freshness_score(item):
    # simple version: newer ID = newer item
    return item["id"] / 100
def user_preference_score(user_id: int, item):
    preferred_categories = get_user_preferred_categories(user_id)
    return 1 if item["category"] in preferred_categories else 0
def score_item(user_id: int, item):
    preference = user_preference_score(user_id, item)
    popularity = get_item_ctr(item["id"])
    freshness = freshness_score(item)

    return (
        0.5 * preference +
        0.3 * popularity +
        0.2 * freshness
    )
def ml_score(item):
    if model is None:
        return 0

    data = pd.DataFrame([{
        "category": item["category"]
    }])

    data = pd.get_dummies(data)

    for col in feature_columns:
        if col not in data:
            data[col] = 0

    data = data[feature_columns]

    return model.predict_proba(data)[0][1]
LAST_MODEL_LOAD_TIME = 0
def load_model():
    global model, feature_columns, LAST_MODEL_LOAD_TIME

    model_mtime = os.path.getmtime(MODEL_PATH)

    if model_mtime != LAST_MODEL_LOAD_TIME:
        print("♻️ Loading new model...")
        model, feature_columns = joblib.load(MODEL_PATH)
        LAST_MODEL_LOAD_TIME = model_mtime

def recommend_for_user(user_id: int):
    load_model()
    items = load_items()

    scored_items = []

    for item in items:
        score = ml_score(item)   # 👈 define score first
        print(item["title"], score)

        item_id = item["id"]
        IMPRESSIONS[item_id] = IMPRESSIONS.get(item_id, 0) + 1

        scored_items.append((score, item))
        # track impression
        item_id = item["id"]
        IMPRESSIONS[item_id] = IMPRESSIONS.get(item_id, 0) + 1

    scored_items.sort(reverse=True, key=lambda x: x[0])

    return [item for _, item in scored_items]




