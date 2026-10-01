from fastapi import APIRouter
from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services import gemini_service, local_model_service

router = APIRouter(prefix="/api", tags=["Concept Explainer"])

@router.post("/explain", response_model=ExplainResponse)
async def explain_concept(payload: ExplainRequest):
    """
    Explains educational concepts for beginner learners.
    Supports 'gemini' API mode or optional 'local' LaMini-Flan-T5 model mode with automatic fallback.
    """
    if payload.mode and payload.mode.lower() == "local":
        result = local_model_service.explain_with_local_model_or_fallback(payload.concept)
    else:
        result = gemini_service.explain_concept(payload.concept)
    
    return ExplainResponse(**result)
