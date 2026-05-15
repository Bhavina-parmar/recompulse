from app.services.rag.embeddings import embed_text
from app.services.rag.vector_store import search

def retrieve_chunks(question, article_id=None):
    q_embedding = embed_text([question])
    results = search(q_embedding, article_id=article_id)
    return results