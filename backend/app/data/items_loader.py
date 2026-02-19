import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "items.json"

def load_items():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
