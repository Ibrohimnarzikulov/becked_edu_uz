"""Reusable DRF permission classes for the users app."""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Faqat admin rolidagi foydalanuvchilar uchun ruxsat."""
    message = "Ruxsat yo'q"

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, 'is_admin', False)
        )
