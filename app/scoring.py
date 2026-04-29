from app.models import Stage


def get_result(home: int, away: int) -> str:
    if home > away:
        return "H"
    elif away > home:
        return "A"
    return "D"


def calculate_bet_points(
    stage: Stage,
    bet_home: int,
    bet_away: int,
    real_home: int,
    real_away: int,
) -> int:
    is_group = stage == Stage.GROUP

    # Placar exato
    if bet_home == real_home and bet_away == real_away:
        return 10 if is_group else 15

    bet_result = get_result(bet_home, bet_away)
    real_result = get_result(real_home, real_away)

    if is_group:
        # Acertou vencedor + diferença de gols
        if bet_result == real_result and (bet_home - bet_away) == (real_home - real_away):
            return 7
        # Acertou apenas vencedor/empate
        if bet_result == real_result:
            return 5
        return 0
    else:
        # Mata-mata: apenas quem avança (sem empate)
        if bet_result == real_result:
            return 8
        return 0


def calculate_special_bet_points(
    champion_id: int | None,
    runner_up_id: int | None,
    third_id: int | None,
    fourth_id: int | None,
    real_champion_id: int | None,
    real_runner_up_id: int | None,
    real_third_id: int | None,
    real_fourth_id: int | None,
) -> int:
    points = 0
    if champion_id and champion_id == real_champion_id:
        points += 30
    if runner_up_id and runner_up_id == real_runner_up_id:
        points += 20
    if third_id and third_id == real_third_id:
        points += 15
    if fourth_id and fourth_id == real_fourth_id:
        points += 10
    return points
