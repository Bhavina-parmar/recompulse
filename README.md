# Recompulse

A full-stack AI-powered content recommendation system with personalized feeds, semantic retrieval, LightGBM ranking, and article-scoped RAG Q&A.

---

## What it does

- Serves a personalized article feed per user using a 3-stage ML pipeline
- Tracks clicks and impressions to continuously improve recommendations
- Auto-retrains the ranking model every 200 events
- Answers questions about a specific article using RAG + Google Gemini
- Falls back to trending + newest articles for new users (cold start)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python |
| ML / Ranking | LightGBM, scikit-learn, pandas |
| Semantic Search | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Index | FAISS |
| RAG LLM | Google Gemini (gemini-2.5-flash) |
| Database | SQLite |
| Frontend | React + Vite |

---

## Project Structure

```
recompulse/
├── backend/
│   ├── app/
│   │   ├── core/          # config, logger
│   │   ├── db/            # SQLite repositories, init, seed
│   │   ├── ml/            # feature builder, model training, evaluation
│   │   ├── models/        # Pydantic models
│   │   ├── routes/        # FastAPI routers
│   │   └── services/
│   │       ├── rag/       # chunker, embeddings, retriever, vector store
│   │       ├── article_rag.py
│   │       ├── recommender.py
│   │       └── semantic_retriever.py
│   ├── scripts/           # one-time data generation scripts
│   ├── recompulse.db
│   ├── model.pkl
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/Feed.jsx
│       ├── api.js
│       └── App.jsx
├── data/
│   └── items.json
└── docs/
    └── architecture.md
```

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```
GOOGLE_API_KEY=your_key_here
```

### Frontend

```bash
cd frontend
npm install
```

---

## First-time Data Setup

Run these scripts once in order from the `backend/` directory:

```bash
# 1. Generate articles into DB
python scripts/generate_articles.py

# 2. Compute and store item embeddings
python scripts/generate_embeddings.py

# 3. Chunk articles for RAG and store in DB
python scripts/generate_article_chunks.py

# 4. Build in-memory FAISS index
python scripts/build_rag_index.py
```

---

## Running

### Backend
```bash
cd backend
uvicorn app.main:app --reload
```
Runs at `http://127.0.0.1:8000`

### Frontend
```bash
cd frontend
npm run dev
```
Runs at `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/recommend/personal?user_id=` | Personalized feed for a user |
| GET | `/recommend/trending` | Trending articles by CTR × time-decay |
| POST | `/event` | Log a click or impression event |
| GET | `/metrics` | Per-item impressions, clicks, CTR, popularity |
| POST | `/article-chat` | Ask a question about a specific article |

### Event payload
```json
{ "user_id": 1, "item_id": 5, "action": "click" }
```

### Article chat payload
```json
{ "article_id": 3, "question": "What does this say about neural networks?" }
```

---

## How Recommendations Work

1. **Retrieval** — Semantic search: user's last 3 clicks → profile embedding → cosine similarity → top 30 candidates
2. **Ranking** — LightGBM scores each candidate on CTR, popularity, category affinity, recency, freshness
3. **Post-processing** — Diversify (max 2 per category) → return top 10

New users (< 3 clicks) get a cold start feed: top 5 trending + 3 newest articles.

See [`docs/architecture.md`](docs/architecture.md) for full system documentation.

---

## Model Retraining

The model retrains automatically every 200 events. To trigger manually:

```bash
cd backend
python -m app.ml.train_model
```
