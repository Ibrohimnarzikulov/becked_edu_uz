#!/usr/bin/env bash
# =============================================================================
# EduHub — lokal kompyuterdan ishlaydi
# Git commit + push + serverda avtomatik deploy (ssh orqali)
# =============================================================================
set -euo pipefail

# ─── Konfiguratsiya (o'zgartiring) ──────────────────────────────────────────
SERVER="${DEPLOY_SERVER:-root@your-server-ip}"   # masalan: root@185.123.45.67
SERVER_PORT="${DEPLOY_SERVER_PORT:-22}"
SSH_KEY="${DEPLOY_SSH_KEY:-$HOME/.ssh/id_rsa}"
REMOTE_DIR="${DEPLOY_REMOTE_DIR:-/opt/eduhub}"
BRANCH="${DEPLOY_BRANCH:-main}"
COMMIT_MSG="${1:-chore: deploy update}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[push]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[err]${NC}  $*" >&2; }

# ─── 0. Tekshirish ──────────────────────────────────────────────────────────
command -v git >/dev/null || { err "git topilmadi"; exit 1; }
[[ -d .git ]] || { err "Bu git repo emas. Avval 'git init' qiling."; exit 1; }

# ─── 1. O'zgarishlarni ko'rsatish ───────────────────────────────────────────
if [[ -z "$(git status --porcelain)" ]]; then
    warn "Hech qanday o'zgarish yo'q. Force push qilinsinmi? (y/N)"
    read -r ans
    [[ "$ans" =~ ^[Yy]$ ]] || { log "Bekor qilindi."; exit 0; }
    FORCE="--force-with-lease"
else
    FORCE=""
fi

# ─── 2. Status ko'rsatish ───────────────────────────────────────────────────
log "O'zgarishlar:"
git status --short

# ─── 3. .env ni tasodifan commit qilmaslik ──────────────────────────────────
if git status --porcelain | grep -qE '^\s*[AM].*\.env$'; then
    err ".env fayl commit qilinmoqda! Avval .gitignore ga qo'shing."
    exit 1
fi

# ─── 4. Add + commit + push ─────────────────────────────────────────────────
log "git add ."
git add .

if [[ -n "$(git status --porcelain)" ]]; then
    log "git commit -m \"$COMMIT_MSG\""
    git commit -m "$COMMIT_MSG" || warn "Commit muvaffaqiyatsiz (bo'sh bo'lishi mumkin)"
else
    log "Yangi commit kerak emas."
fi

log "git push origin $BRANCH $FORCE"
git push origin "$BRANCH" $FORCE

# ─── 5. Serverda deploy ishga tushirish ─────────────────────────────────────
log "Serverga ulanish: $SERVER"
ssh -i "$SSH_KEY" -p "$SERVER_PORT" "$SERVER" "cd $REMOTE_DIR && bash scripts/deploy.sh"

log "✅ Push + deploy yakunlandi."
log "Admin panel: http://$SERVER/admin/  (yoki HTTPS domen)"
