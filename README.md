# EduHub Backend (becked_edu_uz)

Django + DRF backend — **server deploy repozitoriyasi**. Serverda shu repo orqali yangilanadi.

## Stack
- Django 5 + Django REST Framework + SimpleJWT
- PostgreSQL 16
- Gunicorn + Nginx (Docker Compose)

## Docker Compose xizmatlari

| Xizmat | Konteyner | Izoh |
|--------|-----------|------|
| `db` | `eduhub_db` | PostgreSQL 16 |
| `backend` | `eduhub_backend` | Django (gunicorn, ichki 8000-port) |
| `nginx` | `eduhub_nginx` | Reverse proxy — **tashqi port `2343`** |

Volume'lar: `eduhub_db_data`, `eduhub_static`, `eduhub_media`.

## Deploy (serverda)

```bash
# 1. Repo (birinchi marta)
git clone https://github.com/Ibrohimnarzikulov/becked_edu_uz.git
cd becked_edu_uz

# 2. .env tayyorlash (namuna: .env.example)
cp .env.example .env
#   SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, DB_* to'ldiring
#   Docker ichida DB_HOST=db bo'lishi kerak

# 3. Ishga tushirish
docker compose up -d --build
```

Keyingi yangilanishlar:
```bash
git pull
docker compose up -d --build
# nginx web IP'ni keshlashi mumkin — kerak bo'lsa:
docker compose up -d --force-recreate nginx
```

Migratsiya va statik fayllar `entrypoint.sh` orqali avtomatik ishga tushadi.

Sayt: `http://<server-ip>:2343/` — API `/api/`, admin panel `/admin/`.

## API bo'limlari
`auth`, `courses`, `payments`, `chat`, `exams` (tests/scores/leaderboard), `school`.
