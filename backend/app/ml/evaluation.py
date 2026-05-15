import random
import math
from collections import defaultdict
from sklearn.metrics import roc_auc_score

def train_test_split(events, test_ratio=0.2):

    user_events = defaultdict(list)

    # Group events by user
    for event in events:
        if event["action"] == "click":
            user_events[event["user_id"]].append(event)

    train = []
    test = []

    for user_id, clicks in user_events.items():

        # Sort by timestamp (important!)
        clicks.sort(key=lambda x: x["timestamp"])

        split_index = int(len(clicks) * (1 - test_ratio))

        train.extend(clicks[:split_index])
        test.extend(clicks[split_index:])

    return train, test



def compute_auc(model, feature_builder, test_events):

    y_true = []
    y_scores = []

    for event in test_events:

        features = feature_builder(event)

        score = model.predict_proba(features)[0][1]

        y_true.append(1)  # click
        y_scores.append(score)

    if len(set(y_true)) < 2:
        return 0.5

    return roc_auc_score(y_true, y_scores)

def precision_at_k(ranked_items, ground_truth_items, k=10):

    ranked_top_k = ranked_items[:k]

    hits = 0

    for item in ranked_top_k:
        if item in ground_truth_items:
            hits += 1

    return hits / k



def ndcg_at_k(ranked_items, ground_truth_items, k=10):

    dcg = 0.0

    for i, item in enumerate(ranked_items[:k]):
        if item in ground_truth_items:
            dcg += 1 / math.log2(i + 2)

    # Ideal DCG
    ideal_hits = min(len(ground_truth_items), k)
    idcg = sum(1 / math.log2(i + 2) for i in range(ideal_hits))

    if idcg == 0:
        return 0

    return dcg / idcg