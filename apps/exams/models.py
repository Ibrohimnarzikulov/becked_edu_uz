"""Models for exams app — mustaqil testlar va natijalar (reyting uchun)."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Test(models.Model):
    """Mustaqil test — o'qituvchi/admin yaratadi. Savollar JSON ko'rinishida.

    questions shakli (frontendga mos):
        [{"q": "Savol matni", "options": ["A", "B", "C", "D"], "answer": 0}, ...]
    """
    TYPE_IT = 'IT'
    TYPE_SCHOOL = 'School'
    TYPE_CHOICES = [
        (TYPE_IT, 'IT'),
        (TYPE_SCHOOL, 'Maktab'),
    ]

    title = models.CharField(_("nomi"), max_length=200)
    subject = models.CharField(_("fan"), max_length=64, blank=True)
    type = models.CharField(_("tur"), max_length=16, choices=TYPE_CHOICES, default=TYPE_IT)
    questions = models.JSONField(_("savollar"), default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_tests'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'id']
        verbose_name = _("Test")
        verbose_name_plural = _("Testlar (mustaqil)")

    def __str__(self):
        return self.title


class Score(models.Model):
    """Foydalanuvchining bir testdagi natijasi (0–100)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_scores'
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='scores')
    score = models.PositiveIntegerField(_("ball"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'test')]
        ordering = ['-updated_at']
        verbose_name = _("Natija")
        verbose_name_plural = _("Natijalar")

    def __str__(self):
        return f'{self.user.username} — {self.test.title}: {self.score}%'
