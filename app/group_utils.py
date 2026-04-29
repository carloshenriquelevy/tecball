from app import models


def calc_standings(group):
    teams = {}
    for gt in group.group_teams:
        teams[gt.team_id] = {
            "team": gt.team,
            "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0,
        }
    for m in group.matches:
        if m.stage != models.Stage.GROUP:
            continue
        if not m.is_finished or m.home_score is None or m.away_score is None:
            continue
        for team_id, gf, ga in [(m.home_team_id, m.home_score, m.away_score),
                                  (m.away_team_id, m.away_score, m.home_score)]:
            if team_id not in teams:
                continue
            s = teams[team_id]
            s["J"] += 1
            s["GP"] += gf
            s["GC"] += ga
            if gf > ga:
                s["V"] += 1
            elif gf == ga:
                s["E"] += 1
            else:
                s["D"] += 1
    result = []
    for s in teams.values():
        s["SG"] = s["GP"] - s["GC"]
        s["P"] = s["V"] * 3 + s["E"]
        result.append(s)
    result.sort(key=lambda x: (-x["P"], -x["SG"], -x["GP"], x["team"].name))
    return result


def group_rounds(matches):
    group_m = sorted(
        [m for m in matches if m.stage == models.Stage.GROUP],
        key=lambda m: m.match_number,
    )
    rounds = {}
    for i, m in enumerate(group_m):
        r = i // 2 + 1
        rounds.setdefault(r, []).append(m)
    return rounds
