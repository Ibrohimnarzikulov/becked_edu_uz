"""URL configuration for config project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('apps.users.urls_auth')),
    path('api/', include('apps.users.urls_users')),
    path('api/courses/', include('apps.courses.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/school/', include('apps.school.urls')),
    path('api/', include('apps.exams.urls')),  # /api/tests/, /api/scores/, /api/leaderboard/
]

# Media files (dev only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
