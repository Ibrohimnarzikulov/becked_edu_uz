"""URLs for users auth."""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    ChangePasswordView,
    AdminUserListView,
    AdminUserDetailView,
    AdminUserUpdateView,
    AdminStatsView,
    AdminBlockUserView,
    AdminCreateUserView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', ChangePasswordView.as_view(), name='change-password'),
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('admin/users/create/', AdminCreateUserView.as_view(), name='admin-create-user'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:user_id>/update/', AdminUserUpdateView.as_view(), name='admin-update-user'),
    path('admin/users/<int:user_id>/block/', AdminBlockUserView.as_view(), name='admin-block-user'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
