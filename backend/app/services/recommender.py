from app.core.logger import get_logger
logger = get_logger("recommender")

import joblib
import pandas as pd
import random
import math
import time
import os
from pathlib import Path
from collections import Counter

from app.services.semantic_retriever import retrieve_candidates_for_user

from app.db.items_repository import get_all_items
from app.db.events_repository import get_all_events
from app.ml.feature_builder import (
    build_item_stats,
    build_user_stats,
    build_user_category_affinity,
    build_user_recency,
    compute_item_freshness
)

# ===============================
# CONFIG
# ===============================

MIN_INTERACTIONS = 3
COLD_START_FEED_SIZE = 6
EPSILON = 0.2

MODEL_PATH = Path("model.pkl")

# ===============================
# LOAD MODEL
# ===============================

try:
    model, feature_columns = joblib.load(MODEL_PATH)
    print("✅ MODEL LOADED SUCCESSFULLY")
except Exception as e:
    print("❌ MODEL LOAD FAILED:", e)
    model = None
    feature_columns = []

LAST_MODEL_LOAD_TIME = 0


def load_model():
    global model, feature_columns, LAST_MODEL_LOAD_TIME

    model_mtime = os.path.getmtime(MODEL_PATH)

    if model_mtime != LAST_MODEL_LOAD_TIME:
        print("♻️ Loading new model...")
        model, feature_columns = joblib.load(MODEL_PATH)
        LAST_MODEL_LOAD_TIME = model_mtime


# ===============================
# HELPER FUNCTIONS
# ===============================

def get_seen_items(user_id, events):
    return {
        e["item_id"]
        for e in events
        if e["user_id"] == user_id and e["action"] == "click"
    }


def get_user_preferred_categories(user_id: int):
    events = get_all_events()

    user_events = [
        e for e in events
        if e["user_id"] == user_id and e["action"] == "click"
    ]

    if not user_events:
        return []

    clicked_item_ids = [e["item_id"] for e in user_events]
    items = get_all_items()

    clicked_categories = [
        item["category"]
        for item in items
        if item["id"] in clicked_item_ids
    ]

    return [cat for cat, _ in Counter(clicked_categories).most_common()]


def ml_score(user_id, item, impressions, clicks, ctr,popularity,
             user_clicks, user_cat_affinity,user_recency):

    if model is None:
        return 0

    now = int(time.time())
    item_age_hours = (now - item["created_at"]) / 3600

    data = pd.DataFrame([{
        "category": item["category"],
        "item_impressions": impressions.get(item["id"], 0),
        "item_clicks": clicks.get(item["id"], 0),
        "item_ctr": ctr.get(item["id"], 0),
        "item_popularity": popularity.get(item["id"], 0),
        "user_recency_hours": user_recency.get(user_id, 999),
        "user_total_clicks": user_clicks.get(user_id, 0),
        "user_category_affinity":
            user_cat_affinity.get(user_id, {}).get(item["category"], 0),
        "item_age_hours": item_age_hours
    }])

    data = pd.get_dummies(data)

    for col in feature_columns:
        if col not in data:
            data[col] = 0

    data = data[feature_columns]

    return model.predict_proba(data)[0][1]


# ===============================
# POST-RANKING FRESHNESS BOOST
# ===============================

def post_freshness_boost(score, created_at, boost_weight=0.15): 
    freshness = compute_item_freshness(created_at)
    return score * (1 + boost_weight * freshness)


# ===============================
# MAIN RECOMMENDER
# ===============================

def retrieve_candidates(user_id: int):
    events = get_all_events()
    items = get_all_items()

    impressions, clicks, ctr , popularity = build_item_stats()
    user_clicks = build_user_stats()
    user_cat_affinity = build_user_category_affinity()

    user_total_clicks = user_clicks.get(user_id, 0)

    # Cold start
    if user_total_clicks < MIN_INTERACTIONS:
        print("🧊 Cold start triggered")
        return cold_start_feed()

    # Otherwise return all items for now
    # (Later we reduce to top 200 etc.)
    return items

def rank_candidates(user_id: int, candidates: list):
    impressions, clicks, ctr, popularity= build_item_stats()
    user_clicks = build_user_stats()
    user_cat_affinity = build_user_category_affinity()
    user_recency = build_user_recency() 

    ranked = []

    for item in candidates:
        score = ml_score(
            user_id,
            item,
            impressions,
            clicks,
            ctr,
            popularity,
            user_clicks,
            user_cat_affinity,
            user_recency
        )

        affinity = user_cat_affinity.get(user_id, {}).get(item["category"], 0)

        ranked.append({
            **item,
            "score": float(score),
            "user_affinity": affinity
        })
        item["explanation"] = {
            "user_category_affinity":
                user_cat_affinity.get(user_id, {})
                .get(item["category"], 0),

            "item_popularity":
                popularity.get(item["id"], 0),

            "item_ctr":
                ctr.get(item["id"], 0)
        }

    ranked.sort(key=lambda x: x["score"], reverse=True)


    return ranked

def post_process(feed: list):
    def diversify(feed, max_same_category=2):
        diversified = []
        category_count = {}

        for item in feed:
            cat = item["category"]
            count = category_count.get(cat, 0)

            if count < max_same_category:
                diversified.append(item)
                category_count[cat] = count + 1

        return diversified

    return diversify(feed)



def recommend_for_user(user_id: int):

    candidates = retrieve_candidates_for_user(user_id)

    # Cold start already returns final feed
    if candidates and "score" in candidates[0]:
        return candidates

    ranked = rank_candidates(user_id, candidates)

    final_feed = post_process(ranked)

    logger.info(f"User {user_id} final feed generated.")

    return final_feed[:10]

# ===============================
# TRENDING (DB BASED)
# ===============================

def get_trending_items():

    items = get_all_items()
    events = get_all_events()

    now = int(time.time())
    DECAY_LAMBDA = 0.05

    last_click_time = {}
    click_counts = {}
    impression_counts = {}

    for event in events:
        item_id = event["item_id"]

        if event["action"] == "impression":
            impression_counts[item_id] = \
                impression_counts.get(item_id, 0) + 1

        if event["action"] == "click":
            click_counts[item_id] = \
                click_counts.get(item_id, 0) + 1

            ts = event["timestamp"]
            if item_id not in last_click_time or \
                    ts > last_click_time[item_id]:
                last_click_time[item_id] = ts

    scored_items = []

    for item in items:
        item_id = item["id"]

        clicks = click_counts.get(item_id, 0)
        impressions = impression_counts.get(item_id, 0)

        ctr = clicks / impressions if impressions > 0 else 0

        last_ts = last_click_time.get(item_id, 0)
        age_hours = (now - last_ts) / 3600 if last_ts > 0 else 9999

        decay = math.exp(-DECAY_LAMBDA * age_hours)
        score = ctr * decay

        scored_items.append((score, item))

    scored_items.sort(reverse=True, key=lambda x: x[0])

    return [item for _, item in scored_items]


# ===============================
# COLD START FEED
# ===============================

def cold_start_feed():
    trending = get_trending_items()
    items = get_all_items()

    newest = sorted(
        items,
        key=lambda x: x["created_at"],
        reverse=True
    )

    pool = trending[:5] + newest[:3]

    seen_ids = set()
    unique = []

    for item in pool:
        if item["id"] not in seen_ids:
            enriched = {
                **item,
                "score": 0.0,
                "user_affinity": 0
            }
            unique.append(enriched)
            seen_ids.add(item["id"])
    return unique[:COLD_START_FEED_SIZE]
