import faiss
import numpy as np

index = None
chunks = []  # list of (article_id, chunk_text)

def build_index(embeddings, text_chunks):
    global index, chunks

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)

    index.add(embeddings)
    chunks = text_chunks  # expects list of (article_id, chunk_text)


def search(query_embedding, top_k=3, article_id=None):
    distances, indices = index.search(query_embedding, len(chunks))

    results = []
    for i in indices[0]:
        chunk_article_id, chunk_text = chunks[i]
        if article_id is None or chunk_article_id == article_id:
            results.append(chunk_text)
        if len(results) >= top_k:
            break

    return results