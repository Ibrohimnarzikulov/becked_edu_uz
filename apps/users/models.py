"""Custom User model for EduHub."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Foydalanuvchi — 3 rol bilan (admin, teacher, student)."""

    ROLE_ADMIN = 'admin'
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_TEACHER, "O'qituvchi"),
        (ROLE_STUDENT, "O'quvchi"),
    ]

    PLAN_FREE = 'free'
    PLAN_STUDENT = 'student'
    PLAN_PREMIUM = 'premium'
    PLAN_CHOICES = [
        (PLAN_FREE, 'Free'),
        (PLAN_STUDENT, 'Student'),
        (PLAN_PREMIUM, 'Premium'),
    ]

    role = models.CharField(
        _('rol'), max_length=16, choices=ROLE_CHOICES, default=ROLE_STUDENT
    )
    full_name = models.CharField(_("to'liq ism"), max_length=120, blank=True)
    avatar = models.ImageField(_("rasm"), upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(_("bio"), max_length=500, blank=True)
    track = models.CharField(_("yo'nalish"), max_length=64, blank=True)
    grade = models.CharField(_("sinf"), max_length=32, blank=True)
    plan = models.CharField(
        _("tarif"), max_length=16, choices=PLAN_CHOICES, default=PLAN_FREE
    )
    # Obuna (hafta/oy/yil) qachon tugashini bildiradi. Bo'sh bo'lsa —
    # muddatsiz (masalan admin qo'lda 'student' qilib qo'ygan bo'lsa).
    plan_expires_at = models.DateTimeField(_("tarif tugash sanasi"), null=True, blank=True)
    is_blocked = models.BooleanField(_("bloklangan"), default=False)

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def is_student_user(self):
        return self.role == self.ROLE_STUDENT

    def sync_plan_expiry(self):
        """Obuna muddati o'tgan bo'lsa — free'ga qaytaradi.

        Fon vazifasi (celery/cron) yo'q loyihada, shuning uchun bu
        kirishga bog'liq (lazy) tekshiruv: `plan` tekshiriladigan har bir
        joyda (kunlik limit, dars ko'rish) chaqiriladi.
        """
        if self.plan != self.PLAN_FREE and self.plan_expires_at and self.plan_expires_at < timezone.now():
            self.plan = self.PLAN_FREE
            self.plan_expires_at = None
            self.save(update_fields=['plan', 'plan_expires_at'])

    def save(self, *args, **kwargs):
        # username har doim kichik harfda
        if self.username:
            self.username = self.username.lower().strip()
        super().save(*args, **kwargs)
