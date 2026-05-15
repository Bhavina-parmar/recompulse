from fastapi import APIRouter
from app.models.event import Event
from app.db.events_repository import log_event
from app.ml.train_model import train

router = APIRouter()

RETRAIN_THRESHOLD = 200
NEW_EVENT_COUNT = 0


@router.post("/event")
def log_event_route(event: Event):
    global NEW_EVENT_COUNT

    log_event(
        user_id=event.user_id,
        item_id=event.item_id,
        action=event.action
    )

    NEW_EVENT_COUNT += 1

    if NEW_EVENT_COUNT >= RETRAIN_THRESHOLD:
        print("🔁 Retraining model...")
        train()
        NEW_EVENT_COUNT = 0

    return {"status": "logged"}