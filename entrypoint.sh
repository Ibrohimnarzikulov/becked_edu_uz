#!/bin/sh
set -e

# ─── Volume egaligini to'g'rilash ─────────────────────────────
# media_volume / static_volume mount qilinganda ular root egaligida
# bo'lishi mumkin. Django foydalanuvchisi yoza olishi uchun egalikni
# to'g'rilaymiz. Bu blok faqat root sifatida ishga tushganda bajariladi.
if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/media/avatars /app/staticfiles
    chown -R django:django /app/media /app/staticfiles || true
    # Skriptni django foydalanuvchisi ostida qayta ishga tushiramiz.
    exec gosu django "$0" "$@"
fi

echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
while ! nc -z "${DB_HOST}" "${DB_PORT}"; do
    sleep 1
done
echo "[entrypoint] PostgreSQL is reachable."

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput || true

exec "$@"
