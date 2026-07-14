"""Models for school app — fanlar, vazifalar, to'garaklar (admin boshqaradi)."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Subject(models.Model):
    """Maktab fani."""
    name = models.CharField(_("nomi"), max_length=100)
    icon = models.CharField(_("emoji"), max_length=8, default='📘')
    progress = models.PositiveIntegerField(_("progress (%)"), default=0)
    order = models.PositiveIntegerField(_("tartib"), default=0)
    is_active = models.BooleanField(_("aktiv"), default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = _("Fan")
        verbose_name_plural = _("Fanlar")

    def __str__(self):
        return self.name


class Assignment(models.Model):
    """Fan bo'yicha vazifa."""
    STATUS_PENDING = 'pending'
    STATUS_SUBMITTED = 'submitted'
    STATUS_LATE = 'late'
    STATUS_DONE = 'done'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Kutilmoqda'),
        (STATUS_SUBMITTED, 'Topshirildi'),
        (STATUS_LATE, 'Kechikkan'),
        (STATUS_DONE, 'Bajarildi'),
        (STATUS_IN_PROGRESS, 'Jarayonda'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(_("nomi"), max_length=200)
    status = models.CharField(_("holat"), max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    order = models.PositiveIntegerField(_("tartib"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = _("Vazifa")
        verbose_name_plural = _("Vazifalar")

    def __str__(self):
        return self.title


class Circle(models.Model):
    """To'garak."""
    name = models.CharField(_("nomi"), max_length=120)
    icon = models.CharField(_("emoji"), max_length=8, default='🎯')
    members = models.PositiveIntegerField(_("a'zolar soni"), default=0)
    schedule = models.CharField(_("jadval"), max_length=120, blank=True)
    order = models.PositiveIntegerField(_("tartib"), default=0)
    is_active = models.BooleanField(_("aktiv"), default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = _("To'garak")
        verbose_name_plural = _("To'garaklar")

    def __str__(self):
        return self.name
