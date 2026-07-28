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

    # ── Obuna muddati (hafta/oy/yil) ─────────────────────
    # "Hammasida imkoniyat teng, faqat vaqt masalasi" — barcha muddatlar
    # bir xil (PLAN_STUDENT) tarifni ochadi, faqat narx va amal qilish
    # muddati farq qiladi.
    DURATION_WEEK = 'week'
    DURATION_MONTH = 'month'
    DURATION_YEAR = 'year'
    DURATION_CHOICES = [
        (DURATION_WEEK, '1 hafta'),
        (DURATION_MONTH, '1 oy'),
        (DURATION_YEAR, '1 yil'),
    ]
    DURATION_PRICES = {
        DURATION_WEEK: 9000,
        DURATION_MONTH: 2100,
        DURATION_YEAR: 50000,
    }
    DURATION_DAYS = {
        DURATION_WEEK: 7,
        DURATION_MONTH: 30,
        DURATION_YEAR: 365,
    }

    KIND_SUBSCRIPTION = 'subscription'
    KIND_COURSE = 'course'
    KIND_CHOICES = [
        (KIND_SUBSCRIPTION, 'Obuna (tarif)'),
        (KIND_COURSE, 'Kurs sotib olish'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    kind = models.CharField(_("turi"), max_length=16, choices=KIND_CHOICES, default=KIND_SUBSCRIPTION)
    # Obuna to'lovida ishlatiladi (kind=subscription).
    plan = models.CharField(_("tarif"), max_length=16, choices=PLAN_CHOICES, blank=True, default='')
    duration = models.CharField(_("muddat"), max_length=8, choices=DURATION_CHOICES, blank=True, default='')
    # Kurs sotib olishda ishlatiladi (kind=course).
    course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments',
        verbose_name=_("kurs"),
    )
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
        if self.kind == self.KIND_COURSE and self.course_id:
            label = self.course.title_uz
        elif self.duration:
            label = self.get_duration_display()
        else:
            label = self.get_plan_display()
        return f"{self.user.username} — {label} ({self.amount} so'm) — {self.get_status_display()}"