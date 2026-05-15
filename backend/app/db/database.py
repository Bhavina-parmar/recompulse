import sqlite3
from pathlib import Path
from app.core.config import settings
# Database file path
BASE_DIR = Path(__file__).resolve().parents[2]

def get_connection():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn