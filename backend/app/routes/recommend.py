from fastapi import APIRouter
from app.services.recommender import (
    recommend_for_user,
    get_trending_items
)

router = APIRouter(prefix="/recommend")


@router.get("/personal")
def recommend_personal(user_id: int):
    items = recommend_for_user(user_id)
    return {
        "type": "personal",
        "user_id": user_id,
        "items": items
    }


@router.get("/trending")
def recommend_trending():
    items = get_trending_items()
    return {
        "type": "trending",
        "items": items
    }



