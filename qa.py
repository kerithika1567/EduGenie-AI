from fastapi import APIRouter
from app.schemas.qa import QARequest, QAResponse
from app.services import gemini_service

router = APIRouter(prefix="/api", tags=["Student Q&A"])

@router.post("/qa", response_model=QAResponse)
async def ask_question(payload: QARequest):
    """
    Answers student questions using Gemini API.
    """
    result = gemini_service.answer_question(
        question=payload.question,
        context=payload.context
    )
    return QAResponse(**result)
