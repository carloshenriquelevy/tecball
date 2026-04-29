from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user_from_cookie
from app.ranking_utils import get_ranking

router = APIRouter(prefix="/ranking", tags=["ranking"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
def ranking(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)

    return templates.TemplateResponse("ranking/index.html", {
        "request": request,
        "user": user,
        "ranking": get_ranking(db),
    })
