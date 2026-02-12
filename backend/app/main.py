from fastapi import FastAPI

app = FastAPI(title="RecomPulse")

@app.get("/")
def health():
    return {"status": "ok"}
