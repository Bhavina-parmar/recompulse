import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib

#from app.db import EVENTS
from app.services.recommender import load_items
import json
from pathlib import Path

EVENTS_FILE = Path("data/events.json")

def generate_training_data():
    if not EVENTS_FILE.exists():
        return pd.DataFrame()

    events = json.loads(EVENTS_FILE.read_text())
    items = load_items()

    rows = []

    for event in events:
        if event["action"] != "click":
            continue

        clicked_item = next(i for i in items if i["id"] == event["item_id"])

        # ✅ positive sample
        rows.append({
            "category": clicked_item["category"],
            "clicked": 1
        })

        # ✅ negative samples (items shown but not clicked)
        for item in items:
            if item["id"] != event["item_id"]:
                rows.append({
                    "category": item["category"],
                    "clicked": 0
                })

    return pd.DataFrame(rows)



def train():
    df = generate_training_data()

    if df.empty:
        print("Not enough data to train.")
        return

    X = pd.get_dummies(df[["category"]])
    y = df["clicked"]

    model = LogisticRegression()
    model.fit(X, y)

    joblib.dump((model, X.columns.tolist()), "model.pkl")

    print("Model trained!")

if __name__ == "__main__":
    train()
