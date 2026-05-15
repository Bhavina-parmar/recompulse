# Recompulse — Architecture

## Table of Contents
1. [DB Schema](#db-schema)
2. [Event System](#event-system)
3. [Recommendation Pipeline](#recommendation-pipeline)
4. [Ranking Flow](#ranking-flow)
5. [RAG System](#rag-system)
6. [Retrieval Flow](#retrieval-flow)

---

## DB Schema

SQLite database at `backend/recompulse.db`.

### `items`
Stores all articles.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| title | TEXT UNIQUE | UNIQUE prevents duplicate seeding |
| category | TEXT | Tech, Business, Health, Sports, Lifestyle |
| content | TEXT | Full article body |
| embedding | TEXT | JSON-serialized float list (384-dim, all-MiniLM-L6-v2) |
| created_at | INTEGER | Unix timestamp |

### `events`
Stores every user interaction.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| user_id | INTEGER | No FK — simulated users for now |
| item_id | INTEGER | FK → items.id |
| action | TEXT | `click` or `impression` |
| timestamp | INTEGER | Unix timestamp, set server-side |

### `article_chunks`
Stores RAG chunks per article.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| article_id | INTEGER | FK → items.id |
| chunk_text | TEXT | 300-token window with 50-token overlap |
| embedding | TEXT | JSON-serialized float list (384-dim) |

---

## Event System

**Route:** `POST /event`
**File:** `backend/app/routes/events.py`

Every user action (click or impression) is sent from the frontend and written to the `events` table via `log_event()` in `events_repository.py`.

```
Frontend click/impression
    → POST /event  { user_id, item_id, action }
    → log_event()  writes to SQLite with server timestamp
    → NEW_EVENT_COUNT++
    → if NEW_EVENT_COUNT >= 200 → trigger train()
```

- Impressions are sent on first feed load per user switch.
- Clicks are sent on every item click, then the feed refreshes.
- Model auto-retrains every 200 new events (threshold in `events.py`).

---

## Recommendation Pipeline

**Route:** `GET /recommend/personal?user_id=`
**Entry point:** `backend/app/services/recommender.py → recommend_for_user()`

Three stages:

```
1. RETRIEVAL
   retrieve_candidates_for_user(user_id)
       → build user profile embedding from last 3 clicked articles
       → cosine similarity against all item embeddings in SQLite
       → return top 30 candidates
       → cold start fallback if user has < 3 clicks

2. RANKING
   rank_candidates(user_id, candidates)
       → score each candidate with LightGBM model
       → features: item CTR, popularity, user category affinity,
                   user recency, item age, item freshness
       → sort by score descending

3. POST-PROCESSING
   post_process(ranked)
       → diversify: max 2 items per category
       → return top 10
```

### Cold Start
Triggered when `user_total_clicks < 3`.
Returns a mix of: top 5 trending items (CTR × time-decay) + 3 newest articles, deduplicated, capped at 6.

### Trending Feed
**Route:** `GET /recommend/trending`
Score = `CTR × exp(-0.05 × age_hours_since_last_click)`
Sorted descending. No personalization.

---

## Ranking Flow

**File:** `backend/app/services/recommender.py → rank_candidates()`
**Model:** LightGBM classifier, stored at `backend/model.pkl`

### Features used per candidate

| Feature | Source |
|---|---|
| category | item field |
| item_impressions | events table |
| item_clicks | events table |
| item_ctr | clicks / impressions |
| item_popularity | item clicks / total clicks |
| item_age_hours | now - item.created_at |
| item_freshness_ml | exp(-0.02 × age_hours) |
| user_recency_hours | hours since user's last click |
| user_total_clicks | count of user's click events |
| user_category_affinity | user's click count for item's category |

Category is one-hot encoded via `pd.get_dummies`. Missing columns are zero-filled to match training feature set.

### Post-ranking freshness boost
After ML scoring, a freshness multiplier is applied:
`final_score = ml_score × (1 + 0.15 × freshness)`

### Model training
**File:** `backend/app/ml/train_model.py`

- Positive samples: user clicked items
- Hard negatives: popular items user didn't click + same-category items user didn't click (up to 4 negatives per positive)
- Train/test split → LightGBM fit → evaluated with NDCG@10 and Precision@10
- Saved to `model.pkl` via joblib
- Auto-reloaded on file modification time change

---

## RAG System

**Route:** `POST /article-chat`  `{ article_id, question }`
**Files:** `backend/app/services/article_rag.py`, `backend/app/services/rag/`

Answers questions scoped to a specific article using Google Gemini.

```
POST /article-chat { article_id, question }
    → generate_article_answer(article_id, question)
    → retrieve_chunks(question, article_id)
        → embed question with all-MiniLM-L6-v2
        → search FAISS index, filter results by article_id
        → return top 3 matching chunks
    → build prompt: "Answer using ONLY this context: {chunks}"
    → call Gemini API (gemini-2.5-flash)
    → return answer text
```

### Chunking strategy
**File:** `backend/app/services/rag/chunker.py`

- Window size: 300 tokens (words)
- Overlap: 50 tokens
- Chunks stored in `article_chunks` table with `article_id` FK

### FAISS index
**File:** `backend/app/services/rag/vector_store.py`

- In-memory `IndexFlatL2`
- Chunks stored as `(article_id, chunk_text)` tuples
- Search scans all results then filters by `article_id`
- Rebuilt by running `backend/scripts/build_rag_index.py`

---

## Retrieval Flow

**File:** `backend/app/services/semantic_retriever.py`

Used by the recommender (not RAG) to narrow candidates before ranking.

```
retrieve_candidates_for_user(user_id, top_k=30)
    → build_user_profile_embedding(user_id)
        → fetch last 3 clicked items (title + content) from DB
        → concatenate into single string
        → encode with all-MiniLM-L6-v2 → 384-dim vector
    → fetch all items + embeddings from SQLite
    → cosine similarity: user_vector · item_vector / (|u| × |i|)
    → sort descending, return top 30
    → fallback: if no clicks → return all items (cold start path)
```

### Scripts (run once / on demand)

| Script | Purpose |
|---|---|
| `scripts/generate_articles.py` | Generate 60 fake articles into DB |
| `scripts/generate_embeddings.py` | Compute + store item embeddings in `items.embedding` |
| `scripts/generate_article_chunks.py` | Chunk articles + store in `article_chunks` table |
| `scripts/build_rag_index.py` | Build in-memory FAISS index from `article_chunks` |

> Run order: `generate_articles` → `generate_embeddings` → `generate_article_chunks` → `build_rag_index`
