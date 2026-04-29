from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models
from app.auth import require_admin
from app.scoring import calculate_bet_points, calculate_special_bet_points
from app.logger import admin_log
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
def admin_home(request: Request, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    total_users = db.query(models.User).count()
    total_bets = db.query(models.Bet).count()
    finished = db.query(models.Match).filter(models.Match.is_finished == True).count()
    total_matches = db.query(models.Match).count()
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "user": admin,
        "total_users": total_users,
        "total_bets": total_bets,
        "finished": finished,
        "total_matches": total_matches,
    })


@router.get("/jogos", response_class=HTMLResponse)
def list_matches(request: Request, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    matches = (
        db.query(models.Match)
        .options(
            joinedload(models.Match.home_team),
            joinedload(models.Match.away_team),
            joinedload(models.Match.group),
        )
        .order_by(models.Match.match_number)
        .all()
    )
    return templates.TemplateResponse("admin/matches.html", {
        "request": request,
        "user": admin,
        "matches": matches,
    })


@router.get("/resultado/{match_id}", response_class=HTMLResponse)
def result_form(match_id: int, request: Request, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    match = (
        db.query(models.Match)
        .options(joinedload(models.Match.home_team), joinedload(models.Match.away_team))
        .filter(models.Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return templates.TemplateResponse("admin/result_form.html", {
        "request": request,
        "user": admin,
        "match": match,
    })


@router.post("/resultado/{match_id}", response_class=HTMLResponse)
def save_result(
    match_id: int,
    request: Request,
    home_score: int = Form(...),
    away_score: int = Form(...),
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    if not (0 <= home_score <= 20) or not (0 <= away_score <= 20):
        raise HTTPException(status_code=400, detail="Placar inválido")

    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    match.home_score = home_score
    match.away_score = away_score
    match.is_finished = True

    bets = db.query(models.Bet).filter(models.Bet.match_id == match_id).all()
    for bet in bets:
        bet.points = calculate_bet_points(
            stage=match.stage,
            bet_home=bet.home_score,
            bet_away=bet.away_score,
            real_home=home_score,
            real_away=away_score,
        )

    db.commit()
    admin_log.info(
        "result_saved match_id=%s score=%s-%s bets_recalculated=%s admin_id=%s",
        match_id, home_score, away_score, len(bets), admin.id,
    )
    return RedirectResponse("/admin/jogos", status_code=302)


@router.get("/usuarios", response_class=HTMLResponse)
def list_users(request: Request, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    users = db.query(models.User).order_by(models.User.name).all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": admin,
        "users": users,
    })


@router.post("/usuarios/{user_id}/toggle-admin")
def toggle_admin(user_id: int, request: Request, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404)
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Você não pode alterar seu próprio perfil")
    target.is_admin = not target.is_admin
    db.commit()
    admin_log.info(
        "toggle_admin target_id=%s is_admin=%s by_admin_id=%s",
        target.id, target.is_admin, admin.id,
    )
    return RedirectResponse("/admin/usuarios", status_code=302)


@router.get("/palpites-especiais", response_class=HTMLResponse)
def special_results(request: Request, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    teams = db.query(models.Team).order_by(models.Team.name).all()
    specials = (
        db.query(models.SpecialBet)
        .options(
            joinedload(models.SpecialBet.user),
            joinedload(models.SpecialBet.champion),
            joinedload(models.SpecialBet.runner_up),
            joinedload(models.SpecialBet.third),
            joinedload(models.SpecialBet.fourth),
        )
        .all()
    )
    return templates.TemplateResponse("admin/special_results.html", {
        "request": request,
        "user": admin,
        "teams": teams,
        "specials": specials,
    })


@router.post("/palpites-especiais/calcular")
def calculate_special(
    request: Request,
    champion_id: int = Form(...),
    runner_up_id: int = Form(...),
    third_id: int = Form(...),
    fourth_id: int = Form(...),
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    ids = [champion_id, runner_up_id, third_id, fourth_id]
    if len(set(ids)) != 4:
        raise HTTPException(status_code=400, detail="Os quatro times devem ser diferentes")
    valid_ids = {t.id for t in db.query(models.Team.id).filter(models.Team.id.in_(ids)).all()}
    if valid_ids != set(ids):
        raise HTTPException(status_code=400, detail="Time inválido")

    specials = db.query(models.SpecialBet).all()
    for s in specials:
        s.points = calculate_special_bet_points(
            s.champion_id, s.runner_up_id, s.third_id, s.fourth_id,
            champion_id, runner_up_id, third_id, fourth_id,
        )
    db.commit()
    admin_log.info(
        "special_calculated champion=%s runner_up=%s third=%s fourth=%s admin_id=%s",
        champion_id, runner_up_id, third_id, fourth_id, admin.id,
    )
    return RedirectResponse("/admin/palpites-especiais", status_code=302)
