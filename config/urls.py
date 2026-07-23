"""URL configuration for config project."""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="EduHub API",
        default_version='v1',
        description=(
            "EduHub o'quv platformasi API.\n\n"
            "Autentifikatsiya: JWT (Bearer token). "
            "`/api/auth/login/` orqali token oling va "
            "`Authorization: Bearer <access_token>` sarlavhasida yuboring."
        ),
        contact=openapi.Contact(email="support@eduhub.uz"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # ── API hujjatlari ─────────────────────────────
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('admin/', admin.site.urls),

    # ── Auth ───────────────────────────────────────
    # Loyihaning o'z endpointlari (register/login/profile/admin) birinchi keladi.
    path('api/auth/', include('apps.users.urls_auth')),
    # dj-rest-auth qo'shimchalari: logout, user, password reset, token verify.
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),

    # ── Applar ─────────────────────────────────────
    path('api/', include('apps.users.urls_users')),
    path('api/courses/', include('apps.courses.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/school/', include('apps.school.urls')),
    path('api/', include('apps.exams.urls')),
]

# Media fayllar (rasmlar) — production'da nginx uzatadi, DEBUG'da Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
