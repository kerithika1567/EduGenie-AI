from fastapi import APIRouter
from app.schemas.quiz import QuizRequest, QuizResponse
from app.services import gemini_service

router = APIRouter(prefix="/api", tags=["Quiz Generator"])

@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    """
    Generates exactly 3 multiple-choice quiz questions with 4 options each.
    """
    # Enforce exactly 3 questions
    result = gemini_service.generate_quiz(
        topic=payload.topic,
        num_questions=3
    )
    return QuizResponse(**result)
