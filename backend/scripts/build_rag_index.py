from app.services.rag.chunker import chunk_text
from app.services.rag.embeddings import embed_text
from app.services.rag.vector_store import build_index

from app.db.items_repository import get_all_items


def build():

    articles = get_all_items()

    all_chunks = []  # list of (article_id, chunk_text)

    for article in articles:
        chunks = chunk_text(article["content"] or "")
        for chunk in chunks:
            all_chunks.append((article["id"], chunk))

    texts = [chunk for _, chunk in all_chunks]
    embeddings = embed_text(texts)

    build_index(embeddings, all_chunks)


if __name__ == "__main__":
    build()