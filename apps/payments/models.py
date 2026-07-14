"""Models for payments app."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def payment_screenshot_path(instance, filename):
    """Screenshot papkasi: payments/2026/06/user_42/screenshot.png"""
    from datetime import date
    today = date.today()
    return f'payments/{today.year}/{today.month:02d}/user_{instance.user_id}/{filename}'


class Payment(models.Model):
    """To'lov so'rovi — admin tasdiqlashi kerak."""

    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Kutilmoqda'),
        (STATUS_CONFIRMED, 'Tasdiqlandi'),
        (STATUS_REJECTED, 'Rad etildi'),
    ]

    PLAN_FREE = 'free'
    PLAN_STUDENT = 'student'
    PLAN_PREMIUM = 'premium'
    PLAN_CHOICES = [
        (PLAN_FREE, 'Free'),
        (PLAN_STUDENT, 'Student'),
        (PLAN_PREMIUM, 'Premium'),
    ]

    PLAN_PRICES = {
        PLAN_FREE: 0,
        PLAN_STUDENT: 75000,
        PLAN_PREMIUM: 150000,
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    plan = models.CharField(_("tarif"), max_length=16, choices=PLAN_CHOICES)
    amount = models.PositiveIntegerField(_("miqdor (so'm)"))
    screenshot = models.ImageField(_("chek rasmi"), upload_to=payment_screenshot_path, blank=True, null=True)
    status = models.CharField(_("holat"), max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.TextField(_("admin izohi"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("To'lov")
        verbose_name_plural = _("To'lovlar")

    def __str__(self):
        return f"{self.user.username} — {self.get_plan_display()} ({self.amount} so'm) — {self.get_status_display()}"