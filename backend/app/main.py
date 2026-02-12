from fastapi import FastAPI
from app.routes.recommend import router as recommend_router

app = FastAPI(title="RecomPulse")

app.include_router(recommend_router)

@app.get("/")
def health():
    return {"status": "ok"}
