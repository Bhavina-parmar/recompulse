import os

class Settings:
    DB_PATH = "recompulse.db"
    GEMINI_MODEL = "gemini-2.5-flash"
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

settings = Settings()