from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models
from app.auth import require_user
from app.ranking_utils import get_ranking
from datetime import datetime, timezone

router = APIRouter(prefix="/jogos", tags=["jogos"])
templates = Jinja2Templates(directory="templates")


def _by_group(matches):
    groups: dict = {}
    for m in matches:
        k = m.group.name if m.group else "—"
        groups.setdefault(k, []).append(m)
    return dict(sorted(groups.items()))


@router.get("", response_class=HTMLResponse)
def jogos(request: Request, db: Session = Depends(get_db), user: models.User = Depends(require_user)):
    now = datetime.now(timezone.utc)

    opts = [
        joinedload(models.Match.home_team),
        joinedload(models.Match.away_team),
        joinedload(models.Match.group),
        joinedload(models.Match.bets).joinedload(models.Bet.user),
    ]

    live_matches = (
        db.query(models.Match)
        .options(*opts)
        .filter(
            models.Match.match_date.isnot(None),
            models.Match.match_date <= now,
            models.Match.is_finished == False,
        )
        .order_by(models.Match.match_date)
        .all()
    )

    finished_matches = (
        db.query(models.Match)
        .options(*opts)
        .filter(models.Match.is_finished == True)
        .order_by(models.Match.match_date)
        .all()
    )

    ranking_rows = get_ranking(db)
    pts_map = {r["id"]: r["total"] for r in ranking_rows}

    users = sorted(
        db.query(models.User).filter(models.User.is_admin == False).all(),
        key=lambda u: pts_map.get(u.id, 0),
        reverse=True,
    )

    last_5 = (
        db.query(models.Match)
        .filter(models.Match.is_finished == True)
        .order_by(models.Match.match_date.desc())
        .limit(5)
        .all()
    )
    last_5_ids = [m.id for m in reversed(last_5)]

    bets_for_dots = (
        db.query(models.Bet.user_id, models.Bet.match_id, models.Bet.points)
        .filter(models.Bet.match_id.in_(last_5_ids))
        .all()
        if last_5_ids else []
    )
    bet_lookup = {(b.user_id, b.match_id): b.points for b in bets_for_dots}

    form_dots = {
        u.id: [
            "green" if bet_lookup.get((u.id, mid)) and bet_lookup[(u.id, mid)] > 0
            else "red" if (u.id, mid) in bet_lookup
            else "gray"
            for mid in last_5_ids
        ]
        for u in users
    }

    ranking_sidebar = [{"user": u, "pts": pts_map.get(u.id, 0)} for u in users]

    return templates.TemplateResponse("jogos.html", {
        "request": request,
        "user": user,
        "live_matches": live_matches,
        "live_by_group": _by_group(live_matches),
        "finished_matches": finished_matches,
        "finished_by_group": _by_group(finished_matches),
        "users": users,
        "current_user_id": user.id,
        "form_dots": form_dots,
        "ranking": ranking_sidebar,
    })
