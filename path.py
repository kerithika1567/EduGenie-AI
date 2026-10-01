from fastapi import APIRouter
from app.schemas.path import PathRequest, PathResponse
from app.services import gemini_service

router = APIRouter(prefix="/api", tags=["Learning Path Generator"])

@router.post("/learning-path", response_model=PathResponse)
async def generate_learning_path(payload: PathRequest):
    """
    Generates a structured beginner-to-advanced learning path.
    """
    result = gemini_service.generate_learning_path(
        topic=payload.topic,
        level=payload.current_level,
        goal=payload.goal
    )
    return PathResponse(**result)
