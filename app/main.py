from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db, engine, Base
from app import models
from app.auth import get_current_user_from_cookie
from app.ranking_utils import get_user_position, get_ranking
from datetime import datetime, timezone, timedelta


def _is_match_open(match: models.Match) -> bool:
    if match.is_finished:
        return False
    if match.match_date:
        now = datetime.now(timezone.utc)
        dt = match.match_date
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return now < dt - timedelta(minutes=5)
    return True
from app.routers import auth, bets, ranking, admin, jogos, tabela, usuarios

import os
if os.getenv("AUTO_MIGRATE", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="TecBall", description="Bolão Copa do Mundo 2026")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def csrf_check(request: Request, call_next):
    if request.method == "POST":
        host = request.headers.get("host", "")
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        if origin:
            # origin = "https://example.com" — deve bater com o host
            origin_host = origin.split("//")[-1].split("/")[0]
            if origin_host != host:
                from fastapi.responses import Response
                return Response("CSRF check failed", status_code=403)
        elif referer:
            if host not in referer:
                from fastapi.responses import Response
                return Response("CSRF check failed", status_code=403)
        # sem Origin nem Referer: navegadores modernos sempre enviam um deles
        # em requisições cross-site; ausência total indica client direto (API/curl)
    return await call_next(request)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(bets.router)
app.include_router(ranking.router)
app.include_router(admin.router)
app.include_router(jogos.router)
app.include_router(tabela.router)


@app.get("/secando")
def redirect_secando():
    return RedirectResponse("/jogos", status_code=301)


@app.get("/resultados")
def redirect_resultados():
    return RedirectResponse("/jogos", status_code=301)
app.include_router(usuarios.router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=302)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    total_pts, position, total_players = get_user_position(db, user.id)

    today_matches = (
        db.query(models.Match)
        .options(
            joinedload(models.Match.home_team),
            joinedload(models.Match.away_team),
            joinedload(models.Match.group),
        )
        .filter(
            models.Match.is_finished == False,
            models.Match.match_date >= today_start,
            models.Match.match_date < today_end,
        )
        .order_by(models.Match.match_date)
        .all()
    )

    next_match = None
    if not today_matches:
        next_match = (
            db.query(models.Match)
            .options(
                joinedload(models.Match.home_team),
                joinedload(models.Match.away_team),
                joinedload(models.Match.group),
            )
            .filter(
                models.Match.is_finished == False,
                models.Match.match_date > now,
            )
            .order_by(models.Match.match_date)
            .first()
        )

    match_ids = [m.id for m in today_matches]
    if next_match:
        match_ids.append(next_match.id)

    user_bets = {}
    if match_ids:
        user_bets = {
            b.match_id: b
            for b in db.query(models.Bet)
            .filter(models.Bet.user_id == user.id, models.Bet.match_id.in_(match_ids))
            .all()
        }

    mini_ranking = get_ranking(db)[:5]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "total_pts": total_pts,
        "position": position,
        "total_players": total_players,
        "today_matches": today_matches,
        "next_match": next_match,
        "user_bets": user_bets,
        "is_match_open": _is_match_open,
        "mini_ranking": mini_ranking,
    })
