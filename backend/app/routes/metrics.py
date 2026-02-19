from fastapi import APIRouter
from app.database import IMPRESSIONS, CLICKS

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    metrics = []

    for item_id, impressions in IMPRESSIONS.items():
        clicks = CLICKS.get(item_id, 0)
        ctr = clicks / impressions if impressions > 0 else 0

        metrics.append({
            "item_id": item_id,
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 3)
        })

    return metrics
