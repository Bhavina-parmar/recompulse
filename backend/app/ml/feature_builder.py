from collections import defaultdict
from app.db.events_repository import get_all_events
from app.db.items_repository import get_all_items
import math
import time

def build_item_stats():
    events = get_all_events()

    impressions = {}
    clicks = {}

    for event in events:
        item_id = event["item_id"]

        impressions[item_id] = impressions.get(item_id, 0) + 1

        if event["action"] == "click":
            clicks[item_id] = clicks.get(item_id, 0) + 1

    total_clicks = sum(clicks.values())

    ctr = {}
    popularity = {}

    for item_id in impressions:
        clk = clicks.get(item_id, 0)
        imp = impressions.get(item_id, 0)

        ctr[item_id] = clk / imp if imp > 0 else 0
        popularity[item_id] = clk / total_clicks if total_clicks > 0 else 0

    return impressions, clicks, ctr, popularity


def build_user_stats():
    events = get_all_events()
    user_clicks = {}

    for event in events:
        if event["action"] == "click":
            uid = event["user_id"]
            user_clicks[uid] = user_clicks.get(uid, 0) + 1

    return user_clicks


def build_user_category_affinity():
    events = get_all_events()
    from app.db.items_repository import get_all_items

    items = get_all_items()
    item_category = {item["id"]: item["category"] for item in items}

    affinity = {}

    for event in events:
        if event["action"] == "click":
            uid = event["user_id"]
            cat = item_category.get(event["item_id"])

            if uid not in affinity:
                affinity[uid] = {}

            affinity[uid][cat] = affinity[uid].get(cat, 0) + 1

    return affinity

def build_user_recency():
    events = get_all_events()

    last_click_time = {}

    for event in events:
        if event["action"] == "click":
            user_id = event["user_id"]
            ts = event["timestamp"]

            if user_id not in last_click_time or ts > last_click_time[user_id]:
                last_click_time[user_id] = ts

    now = int(time.time())
    recency = {}

    for user_id, ts in last_click_time.items():
        recency[user_id] = (now - ts) / 3600  # hours

    return recency
def compute_item_freshness(created_at, decay_lambda=0.02):
    now = int(time.time())
    age_hours = (now - created_at) / 3600
    return math.exp(-decay_lambda * age_hours)