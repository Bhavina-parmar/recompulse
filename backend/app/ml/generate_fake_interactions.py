import random
import time
import math

from app.db.items_repository import get_all_items
from app.db.events_repository import insert_event

def generate_fake_data(
    num_users=100,
    min_clicks=10,
    max_clicks=25
):
    print("🚀 Generating realistic synthetic interactions...")

    items = get_all_items()
    if not items:
        print("⚠️ No items found in DB.")
        return

    now = int(time.time())
    total_events = 0

    # Group items by category
    category_map = {}
    for item in items:
        category_map.setdefault(item["category"], []).append(item)

    categories = list(category_map.keys())

    # Simulate trending items (20%)
    trending_items = random.sample(
        items,
        max(1, len(items) // 5)
    )

    for user_id in range(1, num_users + 1):

        preferred_category = random.choice(categories)
        num_clicks = random.randint(min_clicks, max_clicks)

        # Simulate activity burst window (last 3–10 days)
        burst_days = random.randint(3, 10)
        burst_start = now - (burst_days * 86400)

        for _ in range(num_clicks):

            r = random.random()

            # 50% preferred category
            if r < 0.5:
                candidate_pool = category_map[preferred_category]

            # 30% trending items
            elif r < 0.8:
                candidate_pool = trending_items

            # 20% random exploration
            else:
                candidate_pool = items

            # Freshness-weighted selection
            weighted_items = []
            for item in candidate_pool:
                age_hours = (now - item["created_at"]) / 3600
                freshness_weight = math.exp(-0.02 * age_hours)
                weighted_items.append((freshness_weight, item))

            total_weight = sum(w for w, _ in weighted_items)
            pick = random.uniform(0, total_weight)

            cumulative = 0
            chosen_item = weighted_items[0][1]

            for weight, item in weighted_items:
                cumulative += weight
                if pick <= cumulative:
                    chosen_item = item
                    break

            # Timestamp mostly inside burst window
            if random.random() < 0.8:
                timestamp = random.randint(burst_start, now)
            else:
                timestamp = now - random.randint(0, 86400 * 30)

            insert_event({
                "user_id": user_id,
                "item_id": chosen_item["id"],
                "action": "click",
                "timestamp": timestamp
            })

            total_events += 1

    print(f"✅ Generated {total_events} realistic click events.")

if __name__ == "__main__":
    generate_fake_data()