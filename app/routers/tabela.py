from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models
from app.auth import require_user
from app.group_utils import group_rounds
from datetime import datetime, timezone, timedelta
import json

router = APIRouter(prefix="/tabela", tags=["tabela"])
templates = Jinja2Templates(directory="templates")


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


@router.get("", response_class=HTMLResponse)
def tabela(request: Request, db: Session = Depends(get_db), user: models.User = Depends(require_user)):
    groups = (
        db.query(models.Group)
        .options(
            joinedload(models.Group.group_teams).joinedload(models.GroupTeam.team),
            joinedload(models.Group.matches).joinedload(models.Match.home_team),
            joinedload(models.Group.matches).joinedload(models.Match.away_team),
        )
        .order_by(models.Group.name)
        .all()
    )

    user_bets = {b.match_id: b for b in db.query(models.Bet).filter(models.Bet.user_id == user.id).all()}

    rounds_by_group = {g.name: group_rounds(g.matches) for g in groups}

    # Serializa dados brutos para o JS calcular a classificação com as
    # regras oficiais da FIFA (Art. 13) — confronto direto, H2H recursivo.
    groups_data = []
    for g in groups:
        group_matches = [m for m in g.matches if m.stage == models.Stage.GROUP]
        groups_data.append({
            "name": g.name,
            "teams": [
                {"id": gt.team_id, "name": gt.team.name, "flag": gt.team.flag}
                for gt in g.group_teams
            ],
            "matches": [
                {
                    "id": m.id,
                    "home_team_id": m.home_team_id,
                    "away_team_id": m.away_team_id,
                    "home_score": m.home_score,
                    "away_score": m.away_score,
                    "is_finished": m.is_finished,
                }
                for m in group_matches
            ],
        })

    return templates.TemplateResponse("tabela.html", {
        "request": request,
        "user": user,
        "groups": groups,
        "user_bets": user_bets,
        "is_match_open": _is_match_open,
        "rounds_by_group": rounds_by_group,
        "groups_json": json.dumps(groups_data, ensure_ascii=False),
    })
