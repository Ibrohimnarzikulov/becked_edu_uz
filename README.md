# 🎓 EduHub Backend

Django REST Framework + PostgreSQL + Docker. **Jazzmin** admin paneli `/admin/` da.

## 🚀 Tez boshlash (serverda)

### 1. Birinchi marta serverga o'rnatish
```bash
# Serverga SSH orqali kiring
ssh root@your-server-ip

# 1.1. Docker o'rnatish (agar yo'q bo'lsa)
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin

# 1.2. Reponi klonlash
git clone https://github.com/Ibrohimnarzikulov/becked_edu_uz.git /opt/eduhub
cd /opt/eduhub

# 1.3. Production .env tayyorlash
cp .env.production .env
nano .env   # SECRET_KEY, parollar va domenni to'ldiring

# 1.4. SECRET_KEY generatsiya qilish
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 1.5. Birinchi deploy
bash scripts/deploy.sh
```

### 2. Keyingi o'zgarishlarni deploy qilish

**Variant A — to'liq avtomatik (lokal kompyuterdan):**
```bash
# Lokal kompyuteringizda
export DEPLOY_SERVER=root@your-server-ip
export DEPLOY_SSH_KEY=~/.ssh/id_rsa
export DEPLOY_REMOTE_DIR=/opt/eduhub

# O'zgarishlar qilingandan keyin
make push MSG="yangi xususiyat qo'shildi"
# yoki
bash scripts/push.sh "yangi xususiyat qo'shildi"
```

**Variant B — serverda qo'lda:**
```bash
ssh root@your-server-ip
cd /opt/eduhub
make pull
```

## 🌐 Admin panel

| Nima | Manzil |
|------|--------|
| Admin panel | `http://your-domain.com:2343/admin/` |
| Login | `.env` dagi `DJANGO_SUPERUSER_USERNAME` |
| Parol | `.env` dagi `DJANGO_SUPERUSER_PASSWORD` |
| API hujjati | `http://your-domain.com:2343/swagger/` |
| API (alternativa) | `http://your-domain.com:2343/redoc/` |

> **Birinchi marta login qilgach, parolni o'zgartirishni UNDTMANG!**

## 🛠 Lokal ishlab chiqish

```bash
# Virtual muhit
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Lokal PostgreSQL kerak (yoki docker compose up db)
cp .env .env.local  # DB_HOST=localhost qilib o'zgartiring

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 📁 Loyiha tuzilmasi

```
becked_edu_uz/
├── apps/
│   ├── core/         # yadro (utils, base)
│   ├── users/        # foydalanuvchilar + auth
│   ├── courses/      # kurslar, darslar, testlar
│   ├── payments/     # to'lovlar
│   ├── chat/         # chat
│   ├── exams/        # imtihonlar
│   └── school/       # maktab
├── config/           # Django settings, urls, wsgi
├── nginx/            # Nginx konfiguratsiya
├── scripts/
│   ├── deploy.sh     # serverda to'liq deploy
│   ├── push.sh       # lokal: git push + serverda deploy
│   └── pull.sh       # serverda: git pull + restart
├── locale/           # tarjimalar
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── .env.production   # production .env namunasi
```

## 🔐 Production checklist

- [ ] `SECRET_KEY` — yangi 64-belgi tasodifiy satr
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` — faqat domen va server IP
- [ ] `DB_PASSWORD` — kuchli parol
- [ ] `DJANGO_SUPERUSER_PASSWORD` — kuchli parol
- [ ] `CORS_ALLOW_ALL=False` + `CORS_ALLOWED_ORIGINS` to'ldirilgan
- [ ] `SECURE_SSL_REDIRECT=True` (HTTPS o'rnatilgach)
- [ ] Let's Encrypt sertifikat o'rnatilgan
- [ ] Firewall: 22, 80, 443, 2343 portlari ochiq
- [ ] `.env` fayl `chmod 600 .env` bilan himoyalangan
