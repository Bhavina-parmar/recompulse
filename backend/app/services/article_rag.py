import os
from google import genai
from app.db.items_repository import get_item_by_id
from app.core.config import settings

from app.core.logger import get_logger
logger = get_logger("article_rag")

client = genai.Client(api_key=settings.GOOGLE_API_KEY)



from app.services.rag.retriever import retrieve_chunks

def generate_article_answer(article_id, question):

    chunks = retrieve_chunks(question, article_id=article_id)

    context = "\n".join(chunks)

    prompt = f"""
    Answer the question using ONLY the context.

    Context:
    {context}

    Question:
    {question}
    """

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"LLM Error: {str(e)}"