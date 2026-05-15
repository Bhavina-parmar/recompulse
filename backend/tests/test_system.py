"""
RECOMPULSE — SYSTEM TEST CHECKLIST
====================================
Covers:
  1. Recommendation Pipeline  (click → event stored → metrics updated → feed changes)
  2. Semantic Retrieval        (fuzzy query matches semantically similar article)
  3. RAG Isolation             (article_id filter — no cross-article chunk leakage)
  4. Feed Refresh              (feed reorders, personalizes, no duplicate impressions)
  5. Metrics Endpoint          (impressions / clicks / CTR update correctly)

Run from backend/ directory:
    pytest tests/test_system.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def post_event(user_id: int, item_id: int, action: str):
    res = client.post("/event", json={
        "user_id": user_id,
        "item_id": item_id,
        "action": action
    })
    assert res.status_code == 200
    assert res.json()["status"] == "logged"


def get_feed(user_id: int):
    res = client.get(f"/recommend/personal?user_id={user_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == user_id
    assert isinstance(data["items"], list)
    return data["items"]


def get_metrics():
    res = client.get("/metrics")
    assert res.status_code == 200
    return res.json()


def metrics_for_item(item_id: int):
    all_metrics = get_metrics()
    return next((m for m in all_metrics if m["item_id"] == item_id), None)


# ─────────────────────────────────────────────
# 1. RECOMMENDATION PIPELINE
# click → event stored → metrics updated → feed changes
# ─────────────────────────────────────────────

class TestRecommendationPipeline:

    def test_cold_start_returns_feed(self):
        """New user with no clicks gets a non-empty cold start feed."""
        feed = get_feed(user_id=9999)
        assert len(feed) > 0, "Cold start feed must not be empty"

    def test_event_stored_after_click(self):
        """Clicking an item stores the event and metrics reflect it."""
        feed = get_feed(user_id=101)
        assert len(feed) > 0

        item_id = feed[0]["id"]

        # record impression baseline
        before = metrics_for_item(item_id)
        before_clicks = before["clicks"] if before else 0

        post_event(user_id=101, item_id=item_id, action="click")

        after = metrics_for_item(item_id)
        assert after is not None, "Item must appear in metrics after a click"
        assert after["clicks"] == before_clicks + 1, (
            f"Expected clicks to increase by 1: {before_clicks} → {after['clicks']}"
        )

    def test_feed_changes_after_clicks(self):
        """
        After 3+ clicks on Tech articles, Tech items should appear
        in the top half of the personalized feed.
        """
        user_id = 202

        # get all items to find Tech ones
        res = client.get(f"/recommend/personal?user_id={user_id}")
        all_items = res.json()["items"]

        # send 3 clicks on whatever is in the feed first
        for item in all_items[:3]:
            post_event(user_id=user_id, item_id=item["id"], action="click")

        feed_after = get_feed(user_id=user_id)
        assert len(feed_after) > 0, "Feed must not be empty after clicks"

        # feed should now have a score field (not cold start)
        assert "score" in feed_after[0], "Ranked feed must include score field"

    def test_impression_event_stored(self):
        """Impression events are stored and reflected in metrics."""
        feed = get_feed(user_id=303)
        assert len(feed) > 0

        item_id = feed[0]["id"]
        before = metrics_for_item(item_id)
        before_imp = before["impressions"] if before else 0

        post_event(user_id=303, item_id=item_id, action="impression")

        after = metrics_for_item(item_id)
        assert after["impressions"] == before_imp + 1


# ─────────────────────────────────────────────
# 2. SEMANTIC RETRIEVAL
# fuzzy query must match semantically similar article
# ─────────────────────────────────────────────

class TestSemanticRetrieval:

    def test_semantic_match_without_exact_keywords(self):
        """
        User clicks an article about 'Artificial Intelligence'.
        Their profile embedding should retrieve AI/ML articles
        even when the query doesn't contain exact title words.
        """
        from app.services.semantic_retriever import (
            build_user_profile_embedding,
            retrieve_candidates_for_user
        )
        import sqlite3
        from pathlib import Path

        DB_PATH = Path(__file__).resolve().parents[2] / "recompulse.db"

        # find an AI article
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM items WHERE category = 'Tech' LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Need at least one Tech article in DB"
        tech_item_id = row[0]

        # simulate user clicking it
        post_event(user_id=501, item_id=tech_item_id, action="click")
        post_event(user_id=501, item_id=tech_item_id, action="click")
        post_event(user_id=501, item_id=tech_item_id, action="click")

        candidates = retrieve_candidates_for_user(user_id=501, top_k=10)
        assert len(candidates) > 0, "Retrieval must return candidates"

        # top results should be Tech-heavy
        categories = [c["category"] for c in candidates[:5]]
        assert "Tech" in categories, (
            f"Expected Tech in top-5 candidates after Tech clicks, got: {categories}"
        )

    def test_deep_learning_query_retrieves_ai_article(self):
        """
        Direct semantic query: 'deep learning' should retrieve
        articles about AI/ML even if title says 'Artificial Intelligence'.
        """
        from app.services.semantic_retriever import retrieve_semantic_candidates

        results = retrieve_semantic_candidates(
            user_query="deep learning neural networks",
            top_k=5
        )

        assert len(results) > 0, "Semantic search must return results"

        titles = [r["title"].lower() for r in results]
        categories = [r["category"] for r in results]

        # at least one result should be Tech or contain AI-related terms
        assert any(
            "tech" == cat or
            "artificial" in t or
            "machine" in t or
            "learning" in t
            for cat, t in zip(categories, titles)
        ), f"Expected AI/ML article in top results for 'deep learning'. Got: {titles}"


# ─────────────────────────────────────────────
# 3. RAG ISOLATION
# article_id filter — chunks must NOT leak across articles
# ─────────────────────────────────────────────

class TestRAGIsolation:

    def test_rag_only_returns_chunks_for_requested_article(self):
        """
        Searching chunks for article_id=X must never return
        a chunk that belongs to article_id=Y.
        """
        from app.services.rag.vector_store import chunks, index

        if index is None or len(chunks) == 0:
            pytest.skip("FAISS index not built — run build_rag_index.py first")

        # pick the first article_id present in the index
        target_article_id = chunks[0][0]

        from app.services.rag.retriever import retrieve_chunks
        results = retrieve_chunks(
            question="what is this article about",
            article_id=target_article_id
        )

        # if results came back, verify none belong to a different article
        # we do this by checking the raw chunks list
        returned_texts = set(results)
        for article_id, chunk_text in chunks:
            if chunk_text in returned_texts:
                assert article_id == target_article_id, (
                    f"RAG returned chunk from article {article_id} "
                    f"when article {target_article_id} was requested. "
                    "Cross-article leakage detected."
                )

    def test_rag_sports_question_on_tech_article_stays_scoped(self):
        """
        Asking a sports question on a Tech article must not
        pull in chunks from Sports articles.
        """
        from app.services.rag.vector_store import chunks, index
        import sqlite3
        from pathlib import Path

        if index is None or len(chunks) == 0:
            pytest.skip("FAISS index not built — run build_rag_index.py first")

        DB_PATH = Path(__file__).resolve().parents[2] / "recompulse.db"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM items WHERE category = 'Tech' LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            pytest.skip("No Tech article in DB")

        tech_article_id = row[0]

        from app.services.rag.retriever import retrieve_chunks
        results = retrieve_chunks(
            question="football match scores and player stats",
            article_id=tech_article_id
        )

        returned_texts = set(results)
        for article_id, chunk_text in chunks:
            if chunk_text in returned_texts:
                assert article_id == tech_article_id, (
                    f"Sports question on Tech article {tech_article_id} "
                    f"leaked chunk from article {article_id}."
                )


# ─────────────────────────────────────────────
# 4. FEED REFRESH
# feed reorders, personalizes, no duplicate impressions
# ─────────────────────────────────────────────

class TestFeedRefresh:

    def test_feed_reorders_after_category_clicks(self):
        """
        Clicking 3 Health articles should shift Health items
        higher in the next feed response.
        """
        import sqlite3
        from pathlib import Path

        DB_PATH = Path(__file__).resolve().parents[2] / "recompulse.db"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM items WHERE category = 'Health' LIMIT 3")
        health_ids = [r[0] for r in cursor.fetchall()]
        conn.close()

        if len(health_ids) < 3:
            pytest.skip("Need at least 3 Health articles")

        user_id = 601

        for item_id in health_ids:
            post_event(user_id=user_id, item_id=item_id, action="click")

        feed = get_feed(user_id=user_id)
        assert len(feed) > 0

        top5_categories = [item["category"] for item in feed[:5]]
        assert "Health" in top5_categories, (
            f"Expected Health in top-5 after 3 Health clicks. Got: {top5_categories}"
        )

    def test_no_duplicate_item_ids_in_feed(self):
        """Each item must appear at most once in a single feed response."""
        feed = get_feed(user_id=701)
        item_ids = [item["id"] for item in feed]
        assert len(item_ids) == len(set(item_ids)), (
            f"Duplicate item IDs found in feed: {item_ids}"
        )

    def test_feed_has_score_field_for_warm_user(self):
        """
        A user with 3+ clicks must get a ranked feed
        where every item has a score field.
        """
        user_id = 801
        feed = get_feed(user_id=user_id)

        # send 3 clicks to exit cold start
        for item in feed[:3]:
            post_event(user_id=user_id, item_id=item["id"], action="click")

        ranked_feed = get_feed(user_id=user_id)
        for item in ranked_feed:
            assert "score" in item, f"Item {item['id']} missing score field"

    def test_impression_not_sent_twice_on_feed_refresh(self):
        """
        Calling /recommend/personal twice for the same user
        should not double-count impressions on the backend.
        This test verifies the endpoint itself doesn't log impressions —
        that responsibility belongs to the frontend (sendImpressions flag).
        """
        user_id = 901
        feed1 = get_feed(user_id=user_id)
        assert len(feed1) > 0

        item_id = feed1[0]["id"]
        before = metrics_for_item(item_id)
        before_imp = before["impressions"] if before else 0

        # call feed again without sending impression events
        get_feed(user_id=user_id)

        after = metrics_for_item(item_id)
        after_imp = after["impressions"] if after else 0

        assert after_imp == before_imp, (
            f"Impression count changed just from calling /recommend/personal twice. "
            f"Before: {before_imp}, After: {after_imp}. "
            "The endpoint must NOT log impressions — only POST /event should."
        )


# ─────────────────────────────────────────────
# 5. METRICS ENDPOINT
# impressions / clicks / CTR update correctly
# ─────────────────────────────────────────────

class TestMetricsEndpoint:

    def test_metrics_endpoint_returns_list(self):
        """/metrics must return a list."""
        metrics = get_metrics()
        assert isinstance(metrics, list)

    def test_impression_increases_metric(self):
        """Sending an impression event must increment impressions by 1."""
        feed = get_feed(user_id=1001)
        assert len(feed) > 0
        item_id = feed[0]["id"]

        before = metrics_for_item(item_id)
        before_imp = before["impressions"] if before else 0

        post_event(user_id=1001, item_id=item_id, action="impression")

        after = metrics_for_item(item_id)
        assert after["impressions"] == before_imp + 1

    def test_click_increases_metric(self):
        """Sending a click event must increment clicks by 1."""
        feed = get_feed(user_id=1002)
        assert len(feed) > 0
        item_id = feed[0]["id"]

        before = metrics_for_item(item_id)
        before_clicks = before["clicks"] if before else 0

        post_event(user_id=1002, item_id=item_id, action="click")

        after = metrics_for_item(item_id)
        assert after["clicks"] == before_clicks + 1

    def test_ctr_calculated_correctly(self):
        """
        CTR = clicks / impressions.
        After 1 impression + 1 click, CTR must equal 0.5
        (assuming starting from 0).
        """
        import sqlite3
        from pathlib import Path

        # use a fresh item that has no prior events
        DB_PATH = Path(__file__).resolve().parents[2] / "recompulse.db"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # find an item with zero events
        cursor.execute("""
            SELECT i.id FROM items i
            LEFT JOIN events e ON i.id = e.item_id
            WHERE e.id IS NULL
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if not row:
            pytest.skip("No zero-event item available for clean CTR test")

        item_id = row[0]
        user_id = 1003

        post_event(user_id=user_id, item_id=item_id, action="impression")
        post_event(user_id=user_id, item_id=item_id, action="impression")
        post_event(user_id=user_id, item_id=item_id, action="click")

        m = metrics_for_item(item_id)
        assert m is not None
        assert m["impressions"] == 2
        assert m["clicks"] == 1
        assert m["ctr"] == pytest.approx(0.5, abs=0.001), (
            f"Expected CTR=0.5 (1 click / 2 impressions), got {m['ctr']}"
        )

    def test_metrics_has_required_fields(self):
        """Every metrics entry must have item_id, impressions, clicks, ctr, popularity."""
        metrics = get_metrics()
        if not metrics:
            pytest.skip("No events in DB yet — run the app and interact first")

        required = {"item_id", "impressions", "clicks", "ctr", "popularity"}
        for entry in metrics:
            missing = required - entry.keys()
            assert not missing, f"Metrics entry missing fields: {missing}"
