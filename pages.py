import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(tags=["Pages"])

@router.get("/", response_class=HTMLResponse)
async def get_index_page(request: Request):
    """
    Renders the main EduGenie frontend application page.
    Uses Starlette 1.x compatible TemplateResponse keyword arguments.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "EduGenie - AI Learning Assistant"}
    )
