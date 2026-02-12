from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.recommend import router as recommend_router
from app.routes.events import router as events_router

app = FastAPI(title="RecomPulse")

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend_router)
app.include_router(events_router)

@app.get("/")
def health():
    return {"status": "ok"}
