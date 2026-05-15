import json
from pathlib import Path
import time

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "events.json"


def load_events():
    if not DATA_PATH.exists():
        return []

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            events = json.load(f)
    except Exception:
        # Corrupted file fallback
        return []

    # Ensure all events have timestamp (backward compatibility)
    updated = False
    for event in events:
        if "timestamp" not in event:
            event["timestamp"] = int(time.time())
            updated = True

    # If we auto-fixed old events, persist them
    if updated:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)

    return events


def save_event(event):
    events = load_events()
    events.append(event)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)