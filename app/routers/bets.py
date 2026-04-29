from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app import models
from app.auth import require_user
from datetime import datetime, timezone, date, timedelta

router = APIRouter(prefix="/palpites", tags=["bets"])
templates = Jinja2Templates(directory="templates")

MAX_SCORE = 20

DAYS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def _day_label(d: date, today: date, tomorrow: date) -> tuple:
    if d == today:
        return ("Hoje", "orange")
    if d == tomorrow:
        return ("Amanhã", "yellow")
    return (f"{d.strftime('%d/%m')} · {DAYS_PT[d.weekday()]}", "default")


def _is_match_open(match: models.Match) -> bool:
    if match.is_finished:
        return False
    if match.match_date:
        now = datetime.now(timezone.utc)
        match_dt = match.match_date
        if match_dt.tzinfo is None:
            match_dt = match_dt.replace(tzinfo=timezone.utc)
        return now < match_dt - timedelta(minutes=5)
    return True


def _are_specials_open(db: Session) -> bool:
    """Palpites especiais fecham quando o primeiro jogo do torneio começa."""
    first_match = (
        db.query(models.Match)
        .filter(models.Match.stage == models.Stage.GROUP, models.Match.match_date.isnot(None))
        .order_by(models.Match.match_date)
        .first()
    )
    if not first_match or not first_match.match_date:
        return True
    match_dt = first_match.match_date
    if match_dt.tzinfo is None:
        match_dt = match_dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < match_dt


@router.get("", response_class=HTMLResponse)
def bets_home(request: Request, db: Session = Depends(get_db), user: models.User = Depends(require_user)):
    now = datetime.now(timezone.utc)
    today = now.date()
    tomorrow = today + timedelta(days=1)

    upcoming = (
        db.query(models.Match)
        .options(
            joinedload(models.Match.home_team),
            joinedload(models.Match.away_team),
            joinedload(models.Match.group),
        )
        .filter(models.Match.is_finished == False)
        .order_by(models.Match.match_date)
        .all()
    )

    user_bets = {b.match_id: b for b in db.query(models.Bet).filter(models.Bet.user_id == user.id).all()}

    # Group by calendar day (UTC), TBD matches at the end
    days: dict = {}
    for m in upcoming:
        if m.match_date:
            dt = m.match_date if m.match_date.tzinfo else m.match_date.replace(tzinfo=timezone.utc)
            day = dt.date()
        else:
            day = None
        days.setdefault(day, []).append(m)

    sorted_days = sorted(days.items(), key=lambda x: (x[0] is None, x[0] or date.max))
    days_labeled = [(d, ms, _day_label(d, today, tomorrow) if d else ("A definir", "gray")) for d, ms in sorted_days]

    total_open = sum(1 for m in upcoming if _is_match_open(m))
    total_bet = sum(1 for m in upcoming if m.id in user_bets and _is_match_open(m))

    return templates.TemplateResponse("bets/index.html", {
        "request": request,
        "user": user,
        "days_labeled": days_labeled,
        "user_bets": user_bets,
        "is_match_open": _is_match_open,
        "total_open": total_open,
        "total_bet": total_bet,
        "now_iso": now.isoformat(),
    })


# ── Especiais ANTES da rota dinâmica /{match_id} ─────────────────────────────

@router.get("/especiais", response_class=HTMLResponse)
def special_bets_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(require_user)):
    teams = db.query(models.Team).order_by(models.Team.name).all()
    special = db.query(models.SpecialBet).filter(models.SpecialBet.user_id == user.id).first()
    specials_open = _are_specials_open(db)
    return templates.TemplateResponse("bets/special.html", {
        "request": request,
        "user": user,
        "teams": teams,
        "special": special,
        "specials_open": specials_open,
    })


@router.post("/especiais", response_class=HTMLResponse)
def save_special_bet(
    request: Request,
    champion_id: int = Form(...),
    runner_up_id: int = Form(...),
    third_id: int = Form(...),
    fourth_id: int = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_user),
):
    if not _are_specials_open(db):
        raise HTTPException(status_code=400, detail="Prazo para palpites especiais encerrado")

    ids = [champion_id, runner_up_id, third_id, fourth_id]

    if len(set(ids)) != 4:
        raise HTTPException(status_code=400, detail="Os quatro times devem ser diferentes")

    valid_ids = {t.id for t in db.query(models.Team.id).filter(models.Team.id.in_(ids)).all()}
    if valid_ids != set(ids):
        raise HTTPException(status_code=400, detail="Time inválido")

    special = db.query(models.SpecialBet).filter(models.SpecialBet.user_id == user.id).first()
    if special:
        special.champion_id = champion_id
        special.runner_up_id = runner_up_id
        special.third_id = third_id
        special.fourth_id = fourth_id
    else:
        special = models.SpecialBet(
            user_id=user.id,
            champion_id=champion_id,
            runner_up_id=runner_up_id,
            third_id=third_id,
            fourth_id=fourth_id,
        )
        db.add(special)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        special = db.query(models.SpecialBet).filter(models.SpecialBet.user_id == user.id).first()
        if special:
            special.champion_id = champion_id
            special.runner_up_id = runner_up_id
            special.third_id = third_id
            special.fourth_id = fourth_id
            db.commit()

    return RedirectResponse("/palpites/especiais", status_code=302)


# ── Rota dinâmica DEPOIS das rotas fixas ─────────────────────────────────────

@router.post("/{match_id}", response_class=HTMLResponse)
def save_bet(
    match_id: int,
    request: Request,
    home_score: int = Form(...),
    away_score: int = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_user),
):
    if not (0 <= home_score <= MAX_SCORE) or not (0 <= away_score <= MAX_SCORE):
        raise HTTPException(status_code=400, detail="Placar inválido")

    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    if not _is_match_open(match):
        raise HTTPException(status_code=400, detail="Prazo para palpite encerrado")

    bet = db.query(models.Bet).filter(models.Bet.user_id == user.id, models.Bet.match_id == match_id).first()
    if bet:
        bet.home_score = home_score
        bet.away_score = away_score
        bet.updated_at = datetime.now(timezone.utc)
    else:
        bet = models.Bet(user_id=user.id, match_id=match_id, home_score=home_score, away_score=away_score)
        db.add(bet)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # corrida entre dois requests: atualiza o que já existe
        bet = db.query(models.Bet).filter(models.Bet.user_id == user.id, models.Bet.match_id == match_id).first()
        if bet:
            bet.home_score = home_score
            bet.away_score = away_score
            bet.updated_at = datetime.now(timezone.utc)
            db.commit()

    return RedirectResponse("/palpites", status_code=302)
