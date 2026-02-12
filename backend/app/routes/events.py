from fastapi import APIRouter
from app.models.event import Event
from app.db import EVENTS

router = APIRouter()

@router.post("/event")
def log_event(event: Event):
    EVENTS.append(event.dict())
    return {
        "status": "logged",
        "total_events": len(EVENTS)
    }
