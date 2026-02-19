import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "events.json"



def load_events():
    if not DATA_PATH.exists():
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_event(event):
    events = load_events()
    events.append(event)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
