from fastapi import APIRouter
from app.services.recommender import recommend_for_user

router = APIRouter()

@router.get("/recommend")
def recommend(user_id: int):
    items = recommend_for_user(user_id)
    return {
        "user_id": user_id,
        "items": items
    }
