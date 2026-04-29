"""
Seed da Copa do Mundo 2026
48 times · 12 grupos · 104 jogos (fase de grupos)
Execute: python seed.py
"""
import os
from app.database import engine, SessionLocal, Base
from app import models
from app.auth import hash_password
from datetime import datetime, timezone

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ─────────────────────────────────────────────
# TIMES (48 seleções confirmadas/prováveis)
# ─────────────────────────────────────────────
teams_data = [
    # CONCACAF (6 vagas + 3 anfitriões)
    ("Estados Unidos", "🇺🇸", "CONCACAF"),
    ("México", "🇲🇽", "CONCACAF"),
    ("Canadá", "🇨🇦", "CONCACAF"),
    ("Panamá", "🇵🇦", "CONCACAF"),
    ("Costa Rica", "🇨🇷", "CONCACAF"),
    ("Jamaica", "🇯🇲", "CONCACAF"),
    # CONMEBOL (6 vagas)
    ("Argentina", "🇦🇷", "CONMEBOL"),
    ("Brasil", "🇧🇷", "CONMEBOL"),
    ("Colômbia", "🇨🇴", "CONMEBOL"),
    ("Equador", "🇪🇨", "CONMEBOL"),
    ("Uruguai", "🇺🇾", "CONMEBOL"),
    ("Venezuela", "🇻🇪", "CONMEBOL"),
    # UEFA (16 vagas)
    ("França", "🇫🇷", "UEFA"),
    ("Espanha", "🇪🇸", "UEFA"),
    ("Alemanha", "🇩🇪", "UEFA"),
    ("Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "UEFA"),
    ("Portugal", "🇵🇹", "UEFA"),
    ("Holanda", "🇳🇱", "UEFA"),
    ("Bélgica", "🇧🇪", "UEFA"),
    ("Itália", "🇮🇹", "UEFA"),
    ("Croácia", "🇭🇷", "UEFA"),
    ("Sérvia", "🇷🇸", "UEFA"),
    ("Dinamarca", "🇩🇰", "UEFA"),
    ("Áustria", "🇦🇹", "UEFA"),
    ("Suíça", "🇨🇭", "UEFA"),
    ("Escócia", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "UEFA"),
    ("Turquia", "🇹🇷", "UEFA"),
    ("Hungria", "🇭🇺", "UEFA"),
    # AFC (8 vagas)
    ("Japão", "🇯🇵", "AFC"),
    ("Coreia do Sul", "🇰🇷", "AFC"),
    ("Austrália", "🇦🇺", "AFC"),
    ("Irã", "🇮🇷", "AFC"),
    ("Arábia Saudita", "🇸🇦", "AFC"),
    ("Iraque", "🇮🇶", "AFC"),
    ("Jordânia", "🇯🇴", "AFC"),
    ("Omã", "🇴🇲", "AFC"),
    # CAF (9 vagas)
    ("Marrocos", "🇲🇦", "CAF"),
    ("Senegal", "🇸🇳", "CAF"),
    ("Nigéria", "🇳🇬", "CAF"),
    ("Costa do Marfim", "🇨🇮", "CAF"),
    ("Gana", "🇬🇭", "CAF"),
    ("Egito", "🇪🇬", "CAF"),
    ("Camarões", "🇨🇲", "CAF"),
    ("Mali", "🇲🇱", "CAF"),
    ("África do Sul", "🇿🇦", "CAF"),
    # OFC (1 vaga)
    ("Nova Zelândia", "🇳🇿", "OFC"),
    # Repescagem inter-confederações (2 vagas)
    ("Paraguai", "🇵🇾", "CONMEBOL"),
    ("Indonésia", "🇮🇩", "AFC"),
]

# Insere times
team_map = {}
for name, flag, conf in teams_data:
    existing = db.query(models.Team).filter(models.Team.name == name).first()
    if not existing:
        t = models.Team(name=name, flag=flag, confederation=conf)
        db.add(t)
        db.flush()
        team_map[name] = t
    else:
        team_map[name] = existing

db.commit()
print(f"✅ {len(team_map)} times cadastrados")

# Recarrega mapa de IDs
team_map = {t.name: t for t in db.query(models.Team).all()}

# ─────────────────────────────────────────────
# GRUPOS A–L (12 grupos de 4 times)
# ─────────────────────────────────────────────
groups_data = {
    "A": ["Estados Unidos", "Panamá", "Nova Zelândia", "Egito"],
    "B": ["México", "Equador", "Sérvia", "Iraque"],
    "C": ["Canadá", "Uruguai", "Dinamarca", "Marrocos"],
    "D": ["Argentina", "Omã", "França", "Camarões"],
    "E": ["Brasil", "Colômbia", "Espanha", "Japão"],
    "F": ["Alemanha", "Holanda", "Costa Rica", "África do Sul"],
    "G": ["Portugal", "Inglaterra", "Venezuela", "Indonésia"],
    "H": ["Bélgica", "Itália", "Arábia Saudita", "Senegal"],
    "I": ["Croácia", "Suíça", "Irã", "Gana"],
    "J": ["Turquia", "Áustria", "Coreia do Sul", "Costa do Marfim"],
    "K": ["Hungria", "Escócia", "Austrália", "Nigéria"],
    "L": ["Paraguai", "Jamaica", "Jordânia", "Mali"],
}

group_map: dict[str, models.Group] = {}
for gname in "ABCDEFGHIJKL":
    existing = db.query(models.Group).filter(models.Group.name == gname).first()
    if not existing:
        g = models.Group(name=gname)
        db.add(g)
        db.flush()
        group_map[gname] = g
    else:
        group_map[gname] = existing

db.commit()

# Associa times aos grupos
for gname, team_names in groups_data.items():
    g = group_map[gname]
    for tname in team_names:
        team = team_map.get(tname)
        if not team:
            print(f"⚠️  Time não encontrado: {tname}")
            continue
        exists = db.query(models.GroupTeam).filter(
            models.GroupTeam.group_id == g.id,
            models.GroupTeam.team_id == team.id
        ).first()
        if not exists:
            db.add(models.GroupTeam(group_id=g.id, team_id=team.id))

db.commit()
print("✅ 12 grupos configurados")

# ─────────────────────────────────────────────
# JOGOS — Fase de Grupos (72 jogos, 3 por grupo)
# Copa 2026 começa em 11/06/2026
# ─────────────────────────────────────────────
match_number = 1

def add_match(group_name, team1_name, team2_name, date_str):
    global match_number
    if db.query(models.Match).filter(models.Match.match_number == match_number).first():
        match_number += 1
        return
    g = group_map[group_name]
    t1 = team_map.get(team1_name)
    t2 = team_map.get(team2_name)
    match_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    m = models.Match(
        match_number=match_number,
        stage=models.Stage.GROUP,
        group_id=g.id,
        home_team_id=t1.id if t1 else None,
        away_team_id=t2.id if t2 else None,
        match_date=match_date,
    )
    db.add(m)
    match_number += 1

# Rodada 1 (Grupos A–L, Jornada 1)
add_match("A", "México", "Nova Zelândia", "2026-06-11 20:00")
add_match("A", "Estados Unidos", "Egito", "2026-06-11 23:00")
add_match("B", "Equador", "Iraque", "2026-06-12 17:00")
add_match("B", "México", "Sérvia", "2026-06-12 20:00")
add_match("C", "Canadá", "Marrocos", "2026-06-12 23:00")
add_match("C", "Uruguai", "Dinamarca", "2026-06-13 17:00")
add_match("D", "Argentina", "Omã", "2026-06-13 20:00")
add_match("D", "França", "Camarões", "2026-06-13 23:00")
add_match("E", "Brasil", "Japão", "2026-06-14 17:00")
add_match("E", "Colômbia", "Espanha", "2026-06-14 20:00")
add_match("F", "Alemanha", "África do Sul", "2026-06-14 23:00")
add_match("F", "Holanda", "Costa Rica", "2026-06-15 17:00")
add_match("G", "Portugal", "Indonésia", "2026-06-15 20:00")
add_match("G", "Inglaterra", "Venezuela", "2026-06-15 23:00")
add_match("H", "Bélgica", "Senegal", "2026-06-16 17:00")
add_match("H", "Itália", "Arábia Saudita", "2026-06-16 20:00")
add_match("I", "Croácia", "Gana", "2026-06-16 23:00")
add_match("I", "Suíça", "Irã", "2026-06-17 17:00")
add_match("J", "Turquia", "Costa do Marfim", "2026-06-17 20:00")
add_match("J", "Áustria", "Coreia do Sul", "2026-06-17 23:00")
add_match("K", "Hungria", "Nigéria", "2026-06-18 17:00")
add_match("K", "Escócia", "Austrália", "2026-06-18 20:00")
add_match("L", "Paraguai", "Jordânia", "2026-06-18 23:00")
add_match("L", "Jamaica", "Mali", "2026-06-19 17:00")

# Rodada 2
add_match("A", "México", "Egito", "2026-06-19 20:00")
add_match("A", "Estados Unidos", "Nova Zelândia", "2026-06-19 23:00")
add_match("B", "Equador", "Sérvia", "2026-06-20 17:00")
add_match("B", "México", "Iraque", "2026-06-20 20:00")
add_match("C", "Canadá", "Dinamarca", "2026-06-20 23:00")
add_match("C", "Uruguai", "Marrocos", "2026-06-21 17:00")
add_match("D", "Argentina", "Camarões", "2026-06-21 20:00")
add_match("D", "França", "Omã", "2026-06-21 23:00")
add_match("E", "Brasil", "Espanha", "2026-06-22 17:00")
add_match("E", "Colômbia", "Japão", "2026-06-22 20:00")
add_match("F", "Alemanha", "Costa Rica", "2026-06-22 23:00")
add_match("F", "Holanda", "África do Sul", "2026-06-23 17:00")
add_match("G", "Portugal", "Venezuela", "2026-06-23 20:00")
add_match("G", "Inglaterra", "Indonésia", "2026-06-23 23:00")
add_match("H", "Bélgica", "Arábia Saudita", "2026-06-24 17:00")
add_match("H", "Itália", "Senegal", "2026-06-24 20:00")
add_match("I", "Croácia", "Irã", "2026-06-24 23:00")
add_match("I", "Suíça", "Gana", "2026-06-25 17:00")
add_match("J", "Turquia", "Coreia do Sul", "2026-06-25 20:00")
add_match("J", "Áustria", "Costa do Marfim", "2026-06-25 23:00")
add_match("K", "Hungria", "Austrália", "2026-06-26 17:00")
add_match("K", "Escócia", "Nigéria", "2026-06-26 20:00")
add_match("L", "Paraguai", "Mali", "2026-06-26 23:00")
add_match("L", "Jamaica", "Jordânia", "2026-06-27 17:00")

# Rodada 3 (jogos simultâneos)
add_match("A", "Estados Unidos", "México", "2026-06-27 20:00")
add_match("A", "Egito", "Nova Zelândia", "2026-06-27 20:00")
add_match("B", "Equador", "México", "2026-06-28 17:00")
add_match("B", "Sérvia", "Iraque", "2026-06-28 17:00")
add_match("C", "Canadá", "Uruguai", "2026-06-28 20:00")
add_match("C", "Dinamarca", "Marrocos", "2026-06-28 20:00")
add_match("D", "Argentina", "França", "2026-06-29 17:00")
add_match("D", "Omã", "Camarões", "2026-06-29 17:00")
add_match("E", "Brasil", "Colômbia", "2026-06-29 20:00")
add_match("E", "Espanha", "Japão", "2026-06-29 20:00")
add_match("F", "Alemanha", "Holanda", "2026-06-30 17:00")
add_match("F", "Costa Rica", "África do Sul", "2026-06-30 17:00")
add_match("G", "Portugal", "Inglaterra", "2026-06-30 20:00")
add_match("G", "Venezuela", "Indonésia", "2026-06-30 20:00")
add_match("H", "Bélgica", "Itália", "2026-07-01 17:00")
add_match("H", "Senegal", "Arábia Saudita", "2026-07-01 17:00")
add_match("I", "Croácia", "Suíça", "2026-07-01 20:00")
add_match("I", "Irã", "Gana", "2026-07-01 20:00")
add_match("J", "Turquia", "Áustria", "2026-07-02 17:00")
add_match("J", "Coreia do Sul", "Costa do Marfim", "2026-07-02 17:00")
add_match("K", "Hungria", "Escócia", "2026-07-02 20:00")
add_match("K", "Austrália", "Nigéria", "2026-07-02 20:00")
add_match("L", "Paraguai", "Jamaica", "2026-07-03 17:00")
add_match("L", "Jordânia", "Mali", "2026-07-03 17:00")

db.commit()
print(f"✅ {match_number - 1} jogos da fase de grupos criados")

# ─────────────────────────────────────────────
# ADMIN padrão
# ─────────────────────────────────────────────
admin_password = os.getenv("ADMIN_PASSWORD")
if not admin_password:
    raise RuntimeError("ADMIN_PASSWORD environment variable is required to seed the admin user")

admin = db.query(models.User).filter(models.User.email == "admin@tecball.com").first()
if not admin:
    admin = models.User(
        name="Admin TecBall",
        email="admin@tecball.com",
        password_hash=hash_password(admin_password),
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    print("✅ Admin criado: admin@tecball.com")
else:
    print("ℹ️  Admin já existe")

db.close()
print("\n🚀 Seed concluído! Rode: uvicorn app.main:app --reload")
