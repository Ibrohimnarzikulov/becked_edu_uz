"""Telegram foydalanuvchisi ↔ EduHub akkaunt bog'lanishi."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TelegramLink(models.Model):
    """Bitta Telegram akkaunt — bitta EduHub foydalanuvchisiga bog'lanadi.

    Bot orqali /start bosib username+parol yuborilganda yaratiladi.
    """
    telegram_id = models.BigIntegerField(_("Telegram ID"), unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_link',
    )
    linked_at = models.DateTimeField(_("bog'langan sana"), auto_now_add=True)

    class Meta:
        verbose_name = _("Telegram bog'lanishi")
        verbose_name_plural = _("Telegram bog'lanishlari")

    def __str__(self):
        return f'{self.user.username} ↔ tg:{self.telegram_id}'
