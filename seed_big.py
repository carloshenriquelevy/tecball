"""
Seed grande: ~50 usuários, 10 novos jogos e apostas geradas automaticamente.
Execute APÓS seed.py e seed_demo.py: python seed_big.py
"""
import random
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal
from app import models
from app.auth import hash_password
from app.scoring import calculate_bet_points

random.seed(42)
db = SessionLocal()
now = datetime.now(timezone.utc)


def rand_score():
    return random.choices([0, 1, 2, 3, 4], weights=[30, 30, 20, 10, 10])[0]


def add_bet(user_id, match_id, hs, aws, is_finished, stage, match_hs, match_aws):
    exists = db.query(models.Bet).filter(
        models.Bet.user_id == user_id,
        models.Bet.match_id == match_id,
    ).first()
    if exists:
        return 0
    pts = (
        calculate_bet_points(stage, hs, aws, match_hs, match_aws)
        if is_finished else None
    )
    db.add(models.Bet(
        user_id=user_id, match_id=match_id,
        home_score=hs, away_score=aws, points=pts,
    ))
    return 1


# ── 45 novos usuários ─────────────────────────────────────────────────────────
new_users_data = [
    ("Bruno Santos",        "bruno@tecball.com"),
    ("Fernanda Lima",       "fernanda@tecball.com"),
    ("Rafael Oliveira",     "rafael@tecball.com"),
    ("Juliana Martins",     "juliana@tecball.com"),
    ("Thiago Pereira",      "thiago@tecball.com"),
    ("Camila Rodrigues",    "camila@tecball.com"),
    ("Diego Ferreira",      "diego@tecball.com"),
    ("Larissa Almeida",     "larissa@tecball.com"),
    ("Felipe Gomes",        "felipe@tecball.com"),
    ("Beatriz Nascimento",  "beatriz@tecball.com"),
    ("Guilherme Ribeiro",   "guilherme@tecball.com"),
    ("Natalia Carvalho",    "natalia@tecball.com"),
    ("Mateus Cardoso",      "mateus@tecball.com"),
    ("Priscila Vieira",     "priscila@tecball.com"),
    ("Rodrigo Araújo",      "rodrigo@tecball.com"),
    ("Amanda Teixeira",     "amanda@tecball.com"),
    ("Leonardo Barbosa",    "leobarbosa@tecball.com"),
    ("Carolina Pinto",      "carolina@tecball.com"),
    ("Eduardo Moraes",      "eduardo@tecball.com"),
    ("Vanessa Ramos",       "vanessa@tecball.com"),
    ("André Correia",       "andre@tecball.com"),
    ("Patrícia Lopes",      "patricia@tecball.com"),
    ("Gabriel Gonçalves",   "gabriel@tecball.com"),
    ("Renata Melo",         "renata@tecball.com"),
    ("Victor Medeiros",     "victor@tecball.com"),
    ("Mariana Freitas",     "mariana@tecball.com"),
    ("Henrique Castro",     "henrique@tecball.com"),
    ("Daniela Cavalcanti",  "daniela@tecball.com"),
    ("Alexandre Nunes",     "alexandre@tecball.com"),
    ("Stephanie Moreira",   "stephanie@tecball.com"),
    ("Igor Machado",        "igor@tecball.com"),
    ("Letícia Dias",        "leticia@tecball.com"),
    ("Marcelo Cunha",       "marcelo@tecball.com"),
    ("Tatiana Monteiro",    "tatiana@tecball.com"),
    ("Roberto Borges",      "roberto@tecball.com"),
    ("Aline Figueiredo",    "aline@tecball.com"),
    ("Samuel Azevedo",      "samuel@tecball.com"),
    ("Viviane Barros",      "viviane@tecball.com"),
    ("Caio Prado",          "caio@tecball.com"),
    ("Elisa Sousa",         "elisa@tecball.com"),
    ("Patrick Campos",      "patrick@tecball.com"),
    ("Marina Rezende",      "marina@tecball.com"),
    ("Davi Tavares",        "davi@tecball.com"),
    ("Isadora Mendonça",    "isadora@tecball.com"),
    ("Leonardo Queiroz",    "lqueiroz@tecball.com"),
]

for name, email in new_users_data:
    if not db.query(models.User).filter(models.User.email == email).first():
        db.add(models.User(name=name, email=email, password_hash=hash_password("senha1234")))

db.commit()

all_users = db.query(models.User).filter(models.User.is_admin == False).all()
print(f"✅ {len(all_users)} usuários no total")

# ── Novos jogos: 8 encerrados + 2 em andamento ───────────────────────────────
#   match_numbers 9–16: encerrados  |  17–18: em andamento
new_match_cfg = {
    9:  (now - timedelta(hours=10), 3, 1,    True),   # Brasil 3-1 Japão
    10: (now - timedelta(hours=9),  0, 2,    True),   # Colômbia 0-2 Espanha
    11: (now - timedelta(hours=8),  2, 0,    True),   # Alemanha 2-0 África do Sul
    12: (now - timedelta(hours=7),  1, 1,    True),   # Holanda 1-1 Costa Rica
    13: (now - timedelta(hours=6),  4, 0,    True),   # Portugal 4-0 Indonésia
    14: (now - timedelta(hours=5),  2, 1,    True),   # Inglaterra 2-1 Venezuela
    15: (now - timedelta(hours=4),  1, 0,    True),   # Bélgica 1-0 Senegal
    16: (now - timedelta(hours=3),  2, 2,    True),   # Itália 2-2 Arábia Saudita
    17: (now - timedelta(minutes=55), None, None, False),  # Croácia vs Gana
    18: (now - timedelta(minutes=20), None, None, False),  # Suíça vs Irã
}

all_match_nums = list(range(1, 19))  # 1-18
matches = {}
for mn in all_match_nums:
    m = db.query(models.Match).filter(models.Match.match_number == mn).first()
    if m:
        matches[mn] = m

for mn, (date, hs, aws, is_fin) in new_match_cfg.items():
    if mn not in matches:
        continue
    m = matches[mn]
    m.match_date = date
    m.home_score = hs
    m.away_score = aws
    m.is_finished = is_fin

db.commit()
print(f"✅ {len(new_match_cfg)} jogos atualizados (matches 9–18)")

# ── Apostas para todos os usuários em todos os 18 jogos ─────────────────────
bet_count = 0
for u in all_users:
    for mn, m in matches.items():
        if random.random() < 0.10:   # ~10% não apostam
            continue
        hs = rand_score()
        aws = rand_score()
        bet_count += add_bet(
            u.id, m.id, hs, aws,
            m.is_finished, m.stage,
            m.home_score, m.away_score,
        )

db.commit()
print(f"✅ {bet_count} apostas inseridas")
db.close()
print(f"\n🚀 Seed grande concluído!")
print(f"   {len(all_users)} usuários · {len(matches)} jogos · {bet_count} apostas")
print(f"   Senha de todos os novos: senha1234")
