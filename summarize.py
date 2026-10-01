from fastapi import APIRouter
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.services import gemini_service

router = APIRouter(prefix="/api", tags=["Text Summarizer"])

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(payload: SummarizeRequest):
    """
    Summarizes study text into concise summary bullet points or paragraphs.
    """
    result = gemini_service.summarize_text(
        text=payload.text,
        length=payload.length
    )
    return SummarizeResponse(**result)
