from fastapi import APIRouter
from app.models.event import Event
from app.db import EVENTS, CLICKS

router = APIRouter()

@router.post("/event")
def log_event(event: Event):
    EVENTS.append(event.dict())

    if event.action == "click":
        CLICKS[event.item_id] = CLICKS.get(event.item_id, 0) + 1

    return {
        "status": "logged",
        "total_events": len(EVENTS)
    }
