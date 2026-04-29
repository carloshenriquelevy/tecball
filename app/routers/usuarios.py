from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models
from app.auth import require_user
from app.ranking_utils import get_ranking
from datetime import datetime, timezone

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
templates = Jinja2Templates(directory="templates")


@router.get("/{target_user_id}", response_class=HTMLResponse)
def user_bets(
    target_user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_user),
):
    target = db.query(models.User).filter(models.User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    now = datetime.now(timezone.utc)

    bets = (
        db.query(models.Bet)
        .join(models.Match)
        .options(
            joinedload(models.Bet.match).joinedload(models.Match.home_team),
            joinedload(models.Bet.match).joinedload(models.Match.away_team),
            joinedload(models.Bet.match).joinedload(models.Match.group),
        )
        .filter(models.Bet.user_id == target_user_id)
        .filter(models.Match.match_date.isnot(None))
        .filter(models.Match.match_date <= now)
        .order_by(models.Match.match_date.desc())
        .all()
    )

    ranking = get_ranking(db)
    position = next((r["position"] for r in ranking if r["id"] == target_user_id), None)
    total_pts = next((r["total"] for r in ranking if r["id"] == target_user_id), 0)
    total_players = len(ranking)

    finished_bets = [b for b in bets if b.match.is_finished]
    inprogress_bets = [b for b in bets if not b.match.is_finished]

    exact_count   = sum(1 for b in finished_bets if b.points is not None and b.points >= 10)
    partial_count = sum(1 for b in finished_bets if b.points is not None and 0 < b.points < 10)
    zero_count    = sum(1 for b in finished_bets if b.points == 0)

    def by_group(bet_list):
        groups: dict = {}
        for b in bet_list:
            k = b.match.group.name if b.match.group else "—"
            groups.setdefault(k, []).append(b)
        return dict(sorted(groups.items()))

    return templates.TemplateResponse("usuarios/apostas.html", {
        "request": request,
        "user": user,
        "target": target,
        "finished_by_group": by_group(finished_bets),
        "inprogress_by_group": by_group(inprogress_bets),
        "finished_bets": finished_bets,
        "inprogress_bets": inprogress_bets,
        "position": position,
        "total_pts": total_pts,
        "total_players": total_players,
        "is_self": user.id == target_user_id,
        "exact_count": exact_count,
        "partial_count": partial_count,
        "zero_count": zero_count,
    })
