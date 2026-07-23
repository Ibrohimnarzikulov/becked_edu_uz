#!/usr/bin/env bash
# =============================================================================
# EduHub — serverda DEBUG=True ga o'tkazish (tezkor CSRF yechimi)
# Ishlatish: ssh root@server 'bash /tmp/fix-debug.sh'
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-~/becked_edu_uz}"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log() { echo -e "${GREEN}[fix]${NC} $*"; }

cd $APP_DIR

# Agar .env yo'q bo'lsa, .env.production dan nusxa olish
if [[ ! -f .env ]]; then
    log ".env topilmadi, .env.production dan nusxa olinmoqda..."
    cp .env.production .env
fi

# DEBUG=False -> DEBUG=True
if grep -q '^DEBUG=False' .env; then
    sed -i 's/^DEBUG=False/DEBUG=True/' .env
    log "✅ DEBUG=True ga o'zgartirildi"
elif grep -q '^DEBUG=True' .env; then
    log "ℹ️  DEBUG allaqachon True"
else
    echo "DEBUG=True" >> .env
    log "✅ DEBUG=True qo'shildi"
fi

# Hozirgi qiymatni ko'rsatish
log "Hozirgi .env holati:"
grep -E "^(DEBUG|ALLOWED_HOSTS|SECURE_SSL|SESSION_COOKIE_SECURE|CSRF_COOKIE_SECURE|CSRF_TRUSTED_ORIGINS)=" .env

# Konteynerni qayta ishga tushirish
log "Backend konteynerini qayta ishga tushirish..."
docker compose restart backend

sleep 3

log "Konteynerlar holati:"
docker compose ps

log "Tekshirish: http://your-server-ip:2343/admin/"
log "Brauzerni yangilang va login qiling."
