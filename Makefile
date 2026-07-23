# EduHub — qulay buyruqlar
# Ishlatish: make <buyruq>

# ─── Lokal ──────────────────────────────────────────────────────────────────
.PHONY: help install run makemigrations migrate shell superuser test clean

help:
	@echo "EduHub buyruqlari:"
	@echo "  make install         — requirements o'rnatish"
	@echo "  make run             — lokal server (port 8000)"
	@echo "  make makemigrations  — yangi migratsiya"
	@echo "  make migrate         — migratsiyalarni qo'llash"
	@echo "  make superuser       — admin yaratish"
	@echo "  make shell           — Django shell"
	@echo "  make test            — testlarni ishga tushirish"
	@echo ""
	@echo "  Docker:"
	@echo "  make up              — docker compose up -d --build"
	@echo "  make down            — docker compose down"
	@echo "  make logs            — konteyner loglari"
	@echo "  make restart         — qayta ishga tushirish"
	@echo "  make admin           — superuser yaratish (docker ichida)"
	@echo ""
	@echo "  Deploy:"
	@echo "  make push MSG='...'  — git push + serverda deploy"
	@echo "  make pull            — serverda qo'lda pull va restart"

install:
	pip install -r requirements.txt

run:
	python manage.py runserver 0.0.0.0:8000

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

superuser:
	python manage.py createsuperuser

shell:
	python manage.py shell

test:
	python manage.py test

# ─── Docker ─────────────────────────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart backend

admin:
	docker compose exec backend python manage.py createsuperuser

# ─── Deploy ─────────────────────────────────────────────────────────────────
push:
	@if [ -z "$(MSG)" ]; then \
		echo "❌ MSG kerak: make push MSG='commit xabari'"; \
		exit 1; \
	fi
	bash scripts/push.sh "$(MSG)"

pull:
	bash scripts/pull.sh
