from sqlalchemy import func
from sqlalchemy.orm import Session
from app import models


def get_ranking(db: Session) -> list[dict]:
    rows = (
        db.query(
            models.User.id,
            models.User.name,
            func.coalesce(func.sum(models.Bet.points), 0).label("bet_pts"),
        )
        .outerjoin(models.Bet, models.Bet.user_id == models.User.id)
        .group_by(models.User.id, models.User.name)
        .all()
    )

    special_points = {
        s.user_id: (s.points or 0)
        for s in db.query(models.SpecialBet).all()
    }

    ranking = []
    for row in rows:
        special_pts = special_points.get(row.id, 0)
        ranking.append({
            "id": row.id,
            "name": row.name,
            "bet_pts": row.bet_pts,
            "special_pts": special_pts,
            "total": row.bet_pts + special_pts,
        })

    ranking.sort(key=lambda x: x["total"], reverse=True)
    for i, r in enumerate(ranking, start=1):
        r["position"] = i

    return ranking


def get_user_position(db: Session, user_id: int) -> tuple[int, int, int]:
    """Returns (total_pts, position, total_players)."""
    ranking = get_ranking(db)
    total_players = len(ranking)
    for r in ranking:
        if r["id"] == user_id:
            return r["total"], r["position"], total_players
    return 0, total_players, total_players
