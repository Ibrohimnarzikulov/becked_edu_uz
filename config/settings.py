"""
Django settings for EduHub backend.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ───────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ── Applications ───────────────────────────────────
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'drf_yasg',
    'django.contrib.humanize',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Local apps
    'apps.core',
    'apps.users',
    'apps.courses',
    'apps.payments',
    'apps.chat',
    'apps.exams',
    'apps.school',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

SITE_ID = 1

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Database ───────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# ── Auth ───────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 4}},
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ── allauth ────────────────────────────────────────
# Ro'yxatdan o'tish faqat username + parol orqali (email talab qilinmaydi).
ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_SIGNUP_FIELDS = ['username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ADAPTER = 'apps.users.adapters.EduHubAccountAdapter'

# ── i18n ───────────────────────────────────────────
LANGUAGE_CODE = config('DEFAULT_LANGUAGE', default='uz')
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('uz', "O'zbekcha"),
    ('ru', 'Русский'),
    ('en', 'English'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ── Static & Media ─────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── DRF ────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── dj-rest-auth ───────────────────────────────────
# Faqat JWT — sessiya/cookie auth ishlatilmaydi.
REST_AUTH = {
    'USE_JWT': True,
    'SESSION_LOGIN': False,
    # DRF'ning Token modeli ishlatilmaydi — faqat JWT.
    'TOKEN_MODEL': None,
    'JWT_AUTH_COOKIE': None,
    'JWT_AUTH_REFRESH_COOKIE': None,
    'JWT_AUTH_HTTPONLY': False,
    'USER_DETAILS_SERIALIZER': 'apps.users.serializers.UserSerializer',
    'REGISTER_SERIALIZER': 'apps.users.serializers.EduHubRegisterSerializer',
}

# Swagger — JWT Bearer tokenni qo'llab-quvvatlash
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "JWT token. Format: `Bearer <access_token>`",
        }
    },
    'USE_SESSION_AUTH': False,
}

# ── CORS ───────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL', default=True, cast=bool)
CORS_ALLOW_CREDENTIALS = True

# Faqat ruxsat berilgan domenlar (CORS_ALLOW_ALL=False bo'lganda ishlaydi)
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=Csv(),
)

# ── Jazzmin ────────────────────────────────────────
JAZZMIN_SETTINGS = {
    'site_title': 'EduHub Admin',
    'site_header': '🎓 EduHub',
    'site_brand': 'EduHub',
    'site_logo': None,
    'welcome_sign': 'EduHub boshqaruv paneli',
    'copyright': 'EduHub © 2026',
    'show_sidebar': True,
    'navigation_expanded': True,
    'default_icon': 'fas fa-graduation-cap',
    'icons': {
        'auth.User': 'fas fa-users',
        'users.User': 'fas fa-user-graduate',
        'courses.Course': 'fas fa-book',
        'courses.Lesson': 'fas fa-play-circle',
        'courses.Test': 'fas fa-question-circle',
        'courses.LessonProgress': 'fas fa-chart-line',
        'payments.Payment': 'fas fa-credit-card',
    },
    'order_with_respect_to': ['users', 'courses', 'payments'],
}

JAZZMIN_UI_THEME = 'darkly'

# Jazzmin — admin paneliga kirish uchun ruxsat berilgan URL'lar
JAZZMIN_LOGIN_URL = '/admin/login/'

# ── Production security (env-driven) ─────────
# Faqat DEBUG=False bo'lganda qo'llaniladi.
# HTTPS proxy orqasida ishlaganda SECURE_SSL_REDIRECT=True qiling.
_IS_PROD = not config('DEBUG', default=False, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = (
    ('HTTP_X_FORWARDED_PROTO', 'https') if _IS_PROD else None
)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=_IS_PROD, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=_IS_PROD, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000 if _IS_PROD else 0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=_IS_PROD, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=_IS_PROD, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# ── CSRF ─────────────────────────────────────────────
# Ishonchli domenlar (HTTPS va reverse-proxy orqali)
# .env ga CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://localhost,http://localhost,http://127.0.0.1',
    cast=Csv(),
)
