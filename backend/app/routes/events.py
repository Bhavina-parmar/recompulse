from fastapi import APIRouter
from app.models.event import Event
from app.db import EVENTS, CLICKS
import json
from pathlib import Path
router = APIRouter()
EVENTS_FILE = Path("data/events.json")
@router.post("/event")
def log_event(event: Event):
    event_dict = event.dict()

    EVENTS.append(event_dict)

    if event.action == "click":
        CLICKS[event.item_id] = CLICKS.get(event.item_id, 0) + 1

    # ✅ persist to file
    if EVENTS_FILE.exists():
        data = json.loads(EVENTS_FILE.read_text())
    else:
        data = []

    data.append(event_dict)
    EVENTS_FILE.write_text(json.dumps(data, indent=2))

    return {
        "status": "logged",
        "total_events": len(EVENTS)
    }
