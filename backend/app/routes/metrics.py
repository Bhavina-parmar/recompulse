from fastapi import APIRouter
from app.ml.feature_builder import build_item_stats

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    impressions, clicks, ctr, popularity = build_item_stats()

    metrics = []

    for item_id, imp in impressions.items():
        metrics.append({
            "item_id": item_id,
            "impressions": imp,
            "clicks": clicks.get(item_id, 0),
            "ctr": round(ctr.get(item_id, 0), 3),
            "popularity": round(popularity.get(item_id, 0), 4)
        })

    return metrics
