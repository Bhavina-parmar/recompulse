from fastapi import APIRouter
from pydantic import BaseModel
from app.services.article_rag import generate_article_answer

router = APIRouter()


class ArticleChatRequest(BaseModel):
    article_id: int
    question: str


@router.post("/article-chat")
def article_chat(request: ArticleChatRequest):
    answer = generate_article_answer(
        request.article_id,
        request.question
    )

    return {
        "article_id": request.article_id,
        "question": request.question,
        "answer": answer
    }