#!/usr/bin/env bash
# =============================================================================
# EduHub — faqat serverda ishlaydi
# Serverda yangi kodni tortib olib, konteynerlarni qayta ishga tushiradi
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/eduhub}"
BRANCH="${BRANCH:-main}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[pull]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }

cd "$APP_DIR"

log "Git pull ($BRANCH)..."
git fetch origin
git reset --hard "origin/$BRANCH"

log "Konteynerlarni qayta build va ishga tushirish..."
docker compose pull || true
docker compose build --no-cache backend
docker compose up -d

log "Migratsiya va static..."
docker compose exec -T backend python manage.py migrate --noinput
docker compose exec -T backend python manage.py collectstatic --noinput

log "Konteynerlar:"
docker compose ps

log "✅ Pull yakunlandi. /admin/ panel tayyor."
