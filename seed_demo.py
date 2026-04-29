"""
Dados de demonstração: usuários, apostas e jogos encerrados/em andamento.
Execute APÓS seed.py: python seed_demo.py
"""
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal
from app import models
from app.auth import hash_password
from app.scoring import calculate_bet_points

db = SessionLocal()
now = datetime.now(timezone.utc)

# ── Usuários ─────────────────────────────────────────────────────────────────

users_data = [
    ("João Silva",      "joao@tecball.com",   "senha1234"),
    ("Maria Fernandes", "maria@tecball.com",  "senha1234"),
    ("Pedro Alves",     "pedro@tecball.com",  "senha1234"),
    ("Ana Costa",       "ana@tecball.com",    "senha1234"),
    ("Lucas Mendes",    "lucas@tecball.com",  "senha1234"),
    ("Carla Souza",     "carla@tecball.com",  "senha1234"),
]

users = {}
for name, email, pwd in users_data:
    u = db.query(models.User).filter(models.User.email == email).first()
    if not u:
        u = models.User(name=name, email=email, password_hash=hash_password(pwd))
        db.add(u)
        db.flush()
    users[email] = u
db.commit()
print(f"✅ {len(users)} usuários prontos")

# ── Jogos: encerrados e em andamento ─────────────────────────────────────────

matches = {
    m.match_number: m
    for m in db.query(models.Match)
    .filter(models.Match.match_number.in_(range(1, 9)))
    .all()
}

# Jogos encerrados (data no passado + resultado)
finished = [
    (1, now - timedelta(hours=6),  2, 0),  # México 2-0 Nova Zelândia
    (2, now - timedelta(hours=5),  1, 1),  # Estados Unidos 1-1 Egito
    (3, now - timedelta(hours=4),  3, 1),  # Equador 3-1 Iraque
    (4, now - timedelta(hours=3),  0, 1),  # México 0-1 Sérvia
    (7, now - timedelta(hours=2),  3, 0),  # Argentina 3-0 Omã
    (8, now - timedelta(hours=1),  2, 2),  # França 2-2 Camarões
]
for num, date, hs, as_ in finished:
    m = matches[num]
    m.match_date = date
    m.home_score = hs
    m.away_score = as_
    m.is_finished = True

# Jogos em andamento (data no passado, sem resultado)
in_progress = [
    (5, now - timedelta(minutes=40)),   # Canadá vs Marrocos
    (6, now - timedelta(minutes=15)),   # Uruguai vs Dinamarca
]
for num, date in in_progress:
    m = matches[num]
    m.match_date = date
    m.is_finished = False
    m.home_score = None
    m.away_score = None

db.commit()
print(f"✅ {len(finished)} jogos encerrados, {len(in_progress)} em andamento")

# ── Apostas ───────────────────────────────────────────────────────────────────
# Formato: match_number → [(email, home, away)]
bets_data = {
    # México 2-0 Nova Zelândia
    1: [
        ("joao@tecball.com",   2, 0),   # 10 pts — placar exato
        ("maria@tecball.com",  1, 0),   #  5 pts — só vencedor
        ("pedro@tecball.com",  3, 1),   #  7 pts — vencedor + mesma dif (2)
        ("ana@tecball.com",    0, 0),   #  0 pts — errou
        ("lucas@tecball.com",  2, 1),   #  5 pts — só vencedor
        ("carla@tecball.com",  1, 2),   #  0 pts — errou
    ],
    # Estados Unidos 1-1 Egito
    2: [
        ("joao@tecball.com",   0, 0),   #  7 pts — empate, dif 0=0
        ("maria@tecball.com",  1, 1),   # 10 pts — placar exato
        ("pedro@tecball.com",  2, 1),   #  0 pts — errou
        ("ana@tecball.com",    1, 1),   # 10 pts — placar exato
        ("lucas@tecball.com",  0, 0),   #  7 pts — empate, dif 0=0
        ("carla@tecball.com",  2, 2),   #  7 pts — empate, dif 0=0
    ],
    # Equador 3-1 Iraque
    3: [
        ("joao@tecball.com",   2, 0),   #  7 pts — vencedor + mesma dif (2)
        ("maria@tecball.com",  1, 0),   #  5 pts — só vencedor
        ("pedro@tecball.com",  3, 1),   # 10 pts — placar exato
        ("ana@tecball.com",    2, 1),   #  5 pts — só vencedor
        ("lucas@tecball.com",  0, 2),   #  0 pts — errou
        ("carla@tecball.com",  1, 0),   #  5 pts — só vencedor
    ],
    # México 0-1 Sérvia
    4: [
        ("joao@tecball.com",   1, 0),   #  0 pts — errou
        ("maria@tecball.com",  0, 1),   # 10 pts — placar exato
        ("pedro@tecball.com",  2, 1),   #  0 pts — errou
        ("ana@tecball.com",    0, 0),   #  0 pts — errou
        ("lucas@tecball.com",  0, 1),   # 10 pts — placar exato
        ("carla@tecball.com",  0, 2),   #  5 pts — só vencedor
    ],
    # Argentina 3-0 Omã
    7: [
        ("joao@tecball.com",   3, 0),   # 10 pts — placar exato
        ("maria@tecball.com",  2, 0),   #  7 pts — vencedor + mesma dif (3 vs... wait 3-0=3, 2-0=2 → different diff → 5 pts)
        ("pedro@tecball.com",  1, 0),   #  5 pts — só vencedor
        ("ana@tecball.com",    2, 0),   #  5 pts — só vencedor (diff 2≠3)
        ("lucas@tecball.com",  3, 0),   # 10 pts — placar exato
        ("carla@tecball.com",  0, 1),   #  0 pts — errou
    ],
    # França 2-2 Camarões
    8: [
        ("joao@tecball.com",   1, 1),   #  7 pts — empate, dif 0=0
        ("maria@tecball.com",  2, 2),   # 10 pts — placar exato
        ("pedro@tecball.com",  3, 0),   #  0 pts — errou
        ("ana@tecball.com",    0, 0),   #  7 pts — empate, dif 0=0
        ("lucas@tecball.com",  1, 2),   #  0 pts — errou
        ("carla@tecball.com",  2, 2),   # 10 pts — placar exato
    ],
    # Canadá vs Marrocos — em andamento, sem pontuação ainda
    5: [
        ("joao@tecball.com",   2, 0),
        ("maria@tecball.com",  1, 1),
        ("pedro@tecball.com",  1, 0),
        ("ana@tecball.com",    0, 0),
        ("lucas@tecball.com",  2, 1),
        ("carla@tecball.com",  0, 1),
    ],
    # Uruguai vs Dinamarca — em andamento, sem pontuação ainda
    6: [
        ("joao@tecball.com",   1, 0),
        ("maria@tecball.com",  2, 2),
        ("pedro@tecball.com",  0, 1),
        ("ana@tecball.com",    1, 1),
        ("lucas@tecball.com",  1, 2),
        ("carla@tecball.com",  2, 0),
    ],
}

bet_count = 0
for match_num, user_bets in bets_data.items():
    m = matches[match_num]
    for email, hs, as_ in user_bets:
        u = users[email]
        existing = db.query(models.Bet).filter(
            models.Bet.user_id == u.id,
            models.Bet.match_id == m.id,
        ).first()
        if existing:
            continue
        pts = calculate_bet_points(m.stage, hs, as_, m.home_score, m.away_score) if m.is_finished else None
        db.add(models.Bet(user_id=u.id, match_id=m.id, home_score=hs, away_score=as_, points=pts))
        bet_count += 1

db.commit()
print(f"✅ {bet_count} apostas inseridas")
db.close()
print("\n🚀 Demo pronto! Acesse http://localhost:8000")
print("   Usuários: joao@tecball.com, maria@tecball.com, ... senha: senha1234")
