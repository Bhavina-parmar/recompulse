from collections import defaultdict
from app.db.events_store import load_events
from app.data.items_loader import load_items

ITEMS = load_items()

def build_item_stats():
    events = load_events()

    impressions = {}
    clicks = {}

    for e in events:
        item = e["item_id"]

        impressions[item] = impressions.get(item, 0) + 1

        if e["action"] == "click":
            clicks[item] = clicks.get(item, 0) + 1

    ctr = {
        item: clicks.get(item, 0) / impressions[item]
        for item in impressions
    }

    return impressions, clicks, ctr


def build_user_stats():
    events = load_events()
    user_clicks = {}

    for e in events:
        if e["action"] == "click":
            user = e["user_id"]
            user_clicks[user] = user_clicks.get(user, 0) + 1

    return user_clicks


def build_user_category_affinity():
    events = load_events()

    user_cat = defaultdict(lambda: defaultdict(int))

    for e in events:
        if e["action"] != "click":
            continue

        user = e["user_id"]
        item_id = e["item_id"]

        item = next(i for i in ITEMS if i["id"] == item_id)
        category = item["category"]

        user_cat[user][category] += 1

    return user_cat
