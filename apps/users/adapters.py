"""allauth adapterlari.

EduHub'da ro'yxatdan o'tish faqat username + parol orqali bo'ladi —
email talab qilinmaydi va tasdiqlash xati yuborilmaydi.
"""
from allauth.account.adapter import DefaultAccountAdapter

from .models import User


class EduHubAccountAdapter(DefaultAccountAdapter):
    """Yangi foydalanuvchi har doim `student` roli bilan yaratiladi."""

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)

        data = form.cleaned_data if hasattr(form, 'cleaned_data') else {}
        user.role = User.ROLE_STUDENT
        user.full_name = (data.get('full_name') or '').strip()
        user.track = data.get('track') or ''
        user.grade = data.get('grade') or ''

        if commit:
            user.save()
        return user

    def send_mail(self, template_prefix, email, context):
        """Email yuborilmaydi — tasdiqlash o'chirilgan."""
        return
