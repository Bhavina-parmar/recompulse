import random
import pandas as pd
import joblib
import time
from pathlib import Path
from collections import defaultdict
from app.db.events_repository import get_all_events
from app.db.items_repository import get_all_items
from app.ml.feature_builder import (
    build_item_stats,
    build_user_stats,
    build_user_category_affinity,
    build_user_recency,
    compute_item_freshness
)
ITEMS = get_all_items()
from app.ml.evaluation import train_test_split, ndcg_at_k, precision_at_k
from lightgbm import LGBMClassifier
random.seed(42)
MODEL_PATH = Path("model.pkl")
def train():

    print("🔁 Starting training with negative sampling...")

    events = get_all_events()
    items = get_all_items()

    if len(events) < 5:
        print("⚠️ Not enough events to train.")
        return

    # ===============================
    # Train/Test Split
    # ===============================

    train_events, test_events = train_test_split(events)

    print(f"Train clicks: {len(train_events)}")
    print(f"Test clicks: {len(test_events)}")

    # ===============================
    # Build Aggregated Stats
    # ===============================

    impressions, clicks, ctr, popularity = build_item_stats()
    user_recency = build_user_recency()
    user_clicks = build_user_stats()
    user_cat_affinity = build_user_category_affinity()

    # ===============================
    # Build Training Dataset
    # ===============================

    user_clicked_items = defaultdict(set)

    for event in train_events:
        user_clicked_items[event["user_id"]].add(event["item_id"])

    rows = []

    for user_id, clicked_items in user_clicked_items.items():

        for item_id in clicked_items:

            item = next((i for i in items if i["id"] == item_id), None)
            if not item:
                continue

            # Positive sample
            rows.append({
                "category": item["category"],
                "item_impressions": impressions.get(item_id, 0),
                "item_clicks": clicks.get(item_id, 0),
                "item_ctr": ctr.get(item_id, 0),
                "item_popularity": popularity.get(item_id, 0),
                "user_recency_hours": user_recency.get(user_id, 999),
                "user_total_clicks": user_clicks.get(user_id, 0),
                "user_category_affinity":
                    user_cat_affinity.get(user_id, {}).get(item["category"], 0),
                "item_freshness_ml": compute_item_freshness(item["created_at"]),
                "label": 1,
            })

            # Negative sampling (2 negatives per positive)
            sorted_popular_items = sorted(
                items,
                key=lambda x: clicks.get(x["id"], 0),
                reverse=True
            )

            hard_negatives = []

            # 1️⃣ Popular items user did NOT click
            for item in sorted_popular_items:
                if item["id"] not in clicked_items:
                    hard_negatives.append(item)
                if len(hard_negatives) >= 2:
                    break

            # 2️⃣ Same category items user did NOT click
            positive_category = item["category"]

            for item in items:
                if (
                    item["category"] == positive_category and
                    item["id"] not in clicked_items
                ):
                    hard_negatives.append(item)

                if len(hard_negatives) >= 4:
                    break


            # Add negative rows
            for neg_item in hard_negatives:

                rows.append({
                    "category": neg_item["category"],
                    "item_impressions":
                        impressions.get(neg_item["id"], 0),
                    "item_clicks":
                        clicks.get(neg_item["id"], 0),
                    "item_ctr":
                        ctr.get(neg_item["id"], 0),
                    "item_popularity":
                        popularity.get(neg_item["id"], 0),  # FIXED
                    "user_recency_hours":
                        user_recency.get(user_id, 999),
                    "user_total_clicks":
                        user_clicks.get(user_id, 0),
                    "user_category_affinity":
                        user_cat_affinity
                        .get(user_id, {})
                        .get(neg_item["category"], 0),
                    "item_freshness_ml": compute_item_freshness(neg_item["created_at"]),
                    "label": 0
                })

    if not rows:
        print("⚠️ Not enough data to build dataset.")
        return

    df = pd.DataFrame(rows)

    print("📊 Training dataset size:", len(df))
    print("📊 Label distribution:")
    print(df["label"].value_counts())

    X = pd.get_dummies(df.drop("label", axis=1))
    y = df["label"]

    model = LGBMClassifier()
    model.fit(X, y)

    feature_columns = X.columns.tolist()
    joblib.dump((model, feature_columns), MODEL_PATH)

    print("✅ Model trained with negatives.")

    # ===============================
    # Evaluation
    # ===============================

    print("📊 Starting evaluation...")

    ndcg_scores = []
    precision_scores = []

    for event in test_events:

        user_id = event["user_id"]
        ground_truth_item = event["item_id"]

        scored_items = []

        for item in items:

            data = pd.DataFrame([{
                "category": item["category"],
                "item_impressions":
                    impressions.get(item["id"], 0),
                "item_clicks":
                    clicks.get(item["id"], 0),
                "item_ctr":
                    ctr.get(item["id"], 0),
                "item_popularity": popularity.get(item["id"], 0),
                "user_recency_hours": user_recency.get(user_id, 999),
                "user_total_clicks":
                    user_clicks.get(user_id, 0),
                "user_category_affinity":
                    user_cat_affinity
                    .get(user_id, {})
                    .get(item["category"], 0),
                "item_freshness_ml": compute_item_freshness(item["created_at"]),
            }])

            data = pd.get_dummies(data)

            for col in feature_columns:
                if col not in data:
                    data[col] = 0

            data = data[feature_columns]

            score = model.predict_proba(data)[0][1]
            scored_items.append((score, item["id"]))

        scored_items.sort(reverse=True)
        ranked_ids = [i[1] for i in scored_items]

        ndcg_scores.append(
            ndcg_at_k(ranked_ids, [ground_truth_item], k=10)
        )

        precision_scores.append(
            precision_at_k(ranked_ids, [ground_truth_item], k=10)
        )

    if ndcg_scores:
        print("📈 NDCG@10:", sum(ndcg_scores) / len(ndcg_scores))
        print("📈 Precision@10:", sum(precision_scores) / len(precision_scores))
    else:
        print("⚠️ Not enough test data to evaluate.")

    print("🎉 Training + evaluation complete.")


if __name__ == "__main__":
    train()
