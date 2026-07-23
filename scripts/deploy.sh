#!/usr/bin/env bash
# =============================================================================
# EduHub — server tomonida to'liq deploy skripti
# Serverda ishlaydi: docker compose up + migratsiya + static + superuser
# =============================================================================
set -euo pipefail

# ─── Konfiguratsiya ─────────────────────────────────────────────────────────
APP_DIR="${APP_DIR:-/opt/eduhub}"
BRANCH="${BRANCH:-main}"
COMPOSE="docker compose"
SERVICE_WEB="backend"
SERVICE_DB="db"

# Ranglar
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[err]${NC}  $*" >&2; }

# ─── 0. Tekshirishlar ───────────────────────────────────────────────────────
[[ -d "$APP_DIR" ]] || { err "$APP_DIR topilmadi. Avval bir marta klon qiling."; exit 1; }
cd "$APP_DIR"

[[ -f .env ]] || { err ".env topilmadi. .env.production dan nusxa oling va to'ldiring."; exit 1; }
[[ -f docker-compose.yml ]] || { err "docker-compose.yml topilmadi."; exit 1; }

# ─── 1. Eng so'nggi kodni olish ─────────────────────────────────────────────
log "Git pull ($BRANCH)..."
git fetch origin
git reset --hard "origin/$BRANCH"

# ─── 2. Eski konteynerlarni to'xtatish ──────────────────────────────────────
log "Eski konteynerlarni to'xtatish..."
$COMPOSE down --remove-orphans || true

# ─── 3. Image qayta build ───────────────────────────────────────────────────
log "Docker image build qilish..."
$COMPOSE build --no-cache "$SERVICE_WEB"

# ─── 4. Servislarni ishga tushirish ─────────────────────────────────────────
log "Servislarni ishga tushirish..."
$COMPOSE up -d

# ─── 5. DB tayyor bo'lishini kutish ──────────────────────────────────────────
log "PostgreSQL tayyor bo'lishini kutish..."
for i in {1..30}; do
    if $COMPOSE exec -T "$SERVICE_DB" pg_isready -U "${DB_USER:-eduhub_user}" >/dev/null 2>&1; then
        log "DB tayyor."
        break
    fi
    sleep 2
    [[ $i -eq 30 ]] && { err "DB 60 soniyada tayyor bo'lmadi."; exit 1; }
done

# ─── 6. Migratsiyalar ───────────────────────────────────────────────────────
log "Migratsiyalar..."
$COMPOSE exec -T "$SERVICE_WEB" python manage.py migrate --noinput

# ─── 7. Static fayllar ──────────────────────────────────────────────────────
log "Collectstatic..."
$COMPOSE exec -T "$SERVICE_WEB" python manage.py collectstatic --noinput

# ─── 8. Superuser (interaktiv bo'lmasa avtomatik yaratadi) ──────────────────
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
    log "Superuser tekshirilmoqda..."
    $COMPOSE exec -T "$SERVICE_WEB" python manage.py shell <<PY
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(
    username="${DJANGO_SUPERUSER_USERNAME}",
    defaults={"email": "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}", "is_superuser": True, "is_staff": True},
)
if created:
    u.set_password("${DJANGO_SUPERUSER_PASSWORD}")
    u.is_superuser = True; u.is_staff = True
    u.save()
    print("Superuser yaratildi:", u.username)
else:
    print("Superuser allaqachon mavjud:", u.username)
PY
fi

# ─── 9. Tekshirish ──────────────────────────────────────────────────────────
log "Konteynerlar holati:"
$COMPOSE ps

log "Backend sog'ligi:"
sleep 3
$COMPOSE exec -T "$SERVICE_WEB" python -c "import django; django.setup()" && log "Django OK" || warn "Django setup tekshiruvi muvaffaqiyatsiz"

# ─── 10. Eski image va containerlarni tozalash ──────────────────────────────
log "Eski imagelarni tozalash..."
docker image prune -f >/dev/null || true

log "✅ Deploy yakunlandi. Admin panel: /admin/"
