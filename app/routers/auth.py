import re
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.auth import hash_password, verify_password, create_access_token, get_current_user_from_cookie
from app.rate_limit import is_rate_limited
from app.logger import auth_log
from app.config import SECURE_COOKIES

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"login:{client_ip}"):
        auth_log.warning("rate_limit ip=%s email=%s", client_ip, email)
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Muitas tentativas. Aguarde 5 minutos."},
            status_code=429,
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        auth_log.warning("login_failed ip=%s email=%s", client_ip, email)
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Email ou senha inválidos"})

    auth_log.info("login_ok user_id=%s email=%s ip=%s", user.id, user.email, client_ip)
    token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        "access_token", token,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    name = name.strip()
    email = email.strip().lower()

    if not name or len(name) < 2:
        return templates.TemplateResponse("auth/register.html", {"request": request, "error": "Nome inválido"})
    if not _EMAIL_RE.match(email):
        return templates.TemplateResponse("auth/register.html", {"request": request, "error": "Email inválido"})
    if len(password) < MIN_PASSWORD_LEN:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": f"Senha deve ter ao menos {MIN_PASSWORD_LEN} caracteres"},
        )

    if db.query(models.User).filter(models.User.email == email).first():
        return templates.TemplateResponse("auth/register.html", {"request": request, "error": "Email já cadastrado"})

    user = models.User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    auth_log.info("register_ok user_id=%s email=%s", user.id, user.email)

    token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        "access_token", token,
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response
