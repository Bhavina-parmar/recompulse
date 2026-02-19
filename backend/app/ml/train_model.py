import time
import joblib
import pandas as pd
import random

from lightgbm import LGBMClassifier

from app.db.events_store import load_events
from app.data.items_loader import load_items

ITEMS = load_items()

from app.ml.feature_builder import (
    build_item_stats,
    build_user_stats,
    build_user_category_affinity
)

random.seed(42)


# -----------------------------
# BUILD SINGLE TRAINING ROW
# -----------------------------
def build_row(
    item,
    user_id,
    label,
    impressions,
    clicks,
    ctr,
    user_clicks,
    user_cat_affinity
):
    return {
        "category": item["category"],
        "item_impressions": impressions.get(item["id"], 0),
        "item_clicks": clicks.get(item["id"], 0),
        "item_ctr": ctr.get(item["id"], 0),
        "user_total_clicks": user_clicks.get(user_id, 0),
        "user_category_affinity": user_cat_affinity.get(user_id, {}).get(item["category"], 0),
        "label": label
    }


# -----------------------------
# TRAIN FUNCTION
# -----------------------------
def train():

    events = load_events()

    if len(events) == 0:
        print("❌ Not enough data to train.")
        return

    impressions, clicks, ctr = build_item_stats()
    user_clicks = build_user_stats()
    user_cat_affinity = build_user_category_affinity()

    rows = []

    # -----------------------------
    # BUILD TRAINING DATA
    # -----------------------------
    for event in events:

        if event["action"] != "click":
            continue

        user_id = event["user_id"]
        clicked_item_id = event["item_id"]

        # 🔹 POSITIVE ITEM (always included)
        positive_item = next(i for i in ITEMS if i["id"] == clicked_item_id)

        rows.append(
            build_row(
                positive_item,
                user_id,
                1,
                impressions,
                clicks,
                ctr,
                user_clicks,
                user_cat_affinity
            )
        )

        # 🔹 NEGATIVE SAMPLING
        negatives = [i for i in ITEMS if i["id"] != clicked_item_id]

        for item in random.sample(negatives, k=min(3, len(negatives))):
            rows.append(
                build_row(
                    item,
                    user_id,
                    0,
                    impressions,
                    clicks,
                    ctr,
                    user_clicks,
                    user_cat_affinity
                )
            )

    if len(rows) == 0:
        print("❌ Not enough rows to train.")
        return

    df = pd.DataFrame(rows)

    print("\n📊 SAMPLE TRAINING DATA")
    print(df.head())

    # -----------------------------
    # SPLIT FEATURES / LABEL
    # -----------------------------
    X = df.drop("label", axis=1)
    y = df["label"]

    print("\n🎯 LABEL DISTRIBUTION")
    print(y.value_counts())

    # ONE HOT ENCODE CATEGORY
    X = pd.get_dummies(X, columns=["category"])

    print("\n🧠 FEATURE VARIATION")
    print(X.nunique())

    if len(y.unique()) < 2:
        print("❌ Not enough class diversity.")
        return

    # -----------------------------
    # TRAIN LIGHTGBM
    # -----------------------------
    model = LGBMClassifier(
        n_estimators=50,
        learning_rate=0.1,
        max_depth=4,
        min_data_in_leaf=1,
        min_data_in_bin=1,
        random_state=42,
        verbosity=-1
    )

    model.fit(X, y)

    print("\n🔥 FEATURE IMPORTANCE")
    print(pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False))

    # -----------------------------
    # SAVE MODEL (VERSIONED)
    # -----------------------------
    model_name = f"model_{int(time.time())}.pkl"

    joblib.dump((model, X.columns.tolist()), model_name)
    joblib.dump((model, X.columns.tolist()), "model.pkl")

    print(f"\n✅ Model trained and saved as {model_name}")


# -----------------------------
# CLI ENTRY
# -----------------------------
if __name__ == "__main__":
    train()
