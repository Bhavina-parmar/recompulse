from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.recommend import router as recommend_router
from app.routes.events import router as events_router
from app.routes.metrics import router as metrics_router
from app.db.init_db import init_db
from app.db.seed_items import seed_items
# from app.routes import article_chat
from app.routes.article_chat import router as article_chat_router
from app.core.config import settings

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(recommend_router)
app.include_router(events_router)
app.include_router(metrics_router)
app.include_router(article_chat_router)

if not settings.GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not set")

init_db()
seed_items()
@app.get("/")
def health():
    return {"status": "ok"}


