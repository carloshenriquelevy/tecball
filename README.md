# TecBall ⚽ — Bolão Copa do Mundo 2026

## Setup rápido

### 1. Criar banco de dados
```bash
psql -U postgres -c "CREATE DATABASE tecball;"
```

### 2. Criar ambiente virtual e instalar dependências
```bash
cd tecball
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente
Copie `.env.example` para `.env` e preencha os valores:
```bash
cp .env.example .env
```

Variáveis obrigatórias:
- `DATABASE_URL` — string de conexão PostgreSQL
- `SECRET_KEY` — chave JWT (gere com `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- `ADMIN_PASSWORD` — senha do usuário admin (usada pelo seed)

### 4. Rodar o seed (times, grupos e jogos)
```bash
ADMIN_PASSWORD=sua_senha_aqui python seed.py
```

### 5. Aplicar migrations do banco
```bash
alembic upgrade head
```

### 6. Iniciar o servidor
```bash
uvicorn app.main:app --reload
```

Acesse: http://localhost:8000

## Login admin padrão
- Email: `admin@tecball.com`
- Senha: definida via `ADMIN_PASSWORD` no passo 4

## Rodando testes
```bash
SECRET_KEY=qualquer pytest tests/
```

## Pontuação
| Situação | Pontos |
|---|---|
| Placar exato (grupos) | 10 |
| Vencedor + diferença de gols (grupos) | 7 |
| Vencedor certo (grupos) | 5 |
| Placar exato (mata-mata) | 15 |
| Classificado certo (mata-mata) | 8 |
| Campeão | 30 |
| Vice-campeão | 20 |
| 3º lugar | 15 |
| 4º lugar | 10 |
