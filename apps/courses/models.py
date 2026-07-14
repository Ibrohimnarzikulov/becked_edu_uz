"""Models for courses app."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    """Kurs — Video darslar to'plami."""

    TYPE_IT = 'IT'
    TYPE_SCHOOL = 'School'
    TYPE_CHOICES = [
        (TYPE_IT, 'IT (Dasturlash)'),
        (TYPE_SCHOOL, 'Maktab'),
    ]

    slug = models.SlugField(_("slug"), max_length=64, unique=True)
    title_uz = models.CharField(_("nomi (uz)"), max_length=120)
    title_ru = models.CharField(_("nomi (ru)"), max_length=120, blank=True)
    title_en = models.CharField(_("nomi (en)"), max_length=120, blank=True)
    icon = models.CharField(_("emoji"), max_length=8, default='📘')
    type = models.CharField(_("tur"), max_length=16, choices=TYPE_CHOICES, default=TYPE_IT)
    order = models.PositiveIntegerField(_("tartib"), default=0)
    is_active = models.BooleanField(_("aktiv"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = _("Kurs")
        verbose_name_plural = _("Kurslar")

    def __str__(self):
        return self.title_uz

    def get_title(self, lang='uz'):
        return getattr(self, f'title_{lang}', None) or self.title_uz


class Lesson(models.Model):
    """Dars — bitta video (YouTube embed)."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title_uz = models.CharField(_("nomi (uz)"), max_length=200)
    title_ru = models.CharField(_("nomi (ru)"), max_length=200, blank=True)
    title_en = models.CharField(_("nomi (en)"), max_length=200, blank=True)
    youtube_id = models.CharField(_("YouTube ID"), max_length=32)
    duration = models.CharField(_("davomiyligi"), max_length=8, default='15:00')
    order = models.PositiveIntegerField(_("tartib"), default=0)

    class Meta:
        ordering = ['course', 'order', 'id']
        verbose_name = _("Dars")
        verbose_name_plural = _("Darslar")

    def __str__(self):
        return f'{self.course.title_uz} — {self.title_uz}'

    def get_title(self, lang='uz'):
        return getattr(self, f'title_{lang}', None) or self.title_uz


class Test(models.Model):
    """Test — bir darsga bir dona test."""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='test')
    title_uz = models.CharField(_("nomi (uz)"), max_length=200)
    title_ru = models.CharField(_("nomi (ru)"), max_length=200, blank=True)
    title_en = models.CharField(_("nomi (en)"), max_length=200, blank=True)
    subject = models.CharField(_("fan"), max_length=64, blank=True)
    type = models.CharField(_("tur"), max_length=16, default='IT')

    class Meta:
        verbose_name = _("Test")
        verbose_name_plural = _("Testlar")

    def __str__(self):
        return self.title_uz


class Question(models.Model):
    """Test savoli — 4 ta variant bilan."""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text_uz = models.TextField(_("savol (uz)"))
    text_ru = models.TextField(_("savol (ru)"), blank=True)
    text_en = models.TextField(_("savol (en)"), blank=True)
    order = models.PositiveIntegerField(_("tartib"), default=0)

    class Meta:
        ordering = ['test', 'order', 'id']
        verbose_name = _("Savol")
        verbose_name_plural = _("Savollar")

    def __str__(self):
        return self.text_uz[:60]

    def get_text(self, lang='uz'):
        return getattr(self, f'text_{lang}', None) or self.text_uz


class Choice(models.Model):
    """Variant — to'g'ri yoki noto'g'ri."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text_uz = models.CharField(_("matn (uz)"), max_length=300)
    text_ru = models.CharField(_("matn (ru)"), max_length=300, blank=True)
    text_en = models.CharField(_("matn (en)"), max_length=300, blank=True)
    is_correct = models.BooleanField(_("to'g'ri"), default=False)
    order = models.PositiveIntegerField(_("tartib"), default=0)

    class Meta:
        ordering = ['question', 'order', 'id']
        verbose_name = _("Variant")
        verbose_name_plural = _("Variantlar")

    def __str__(self):
        return self.text_uz[:60]

    def get_text(self, lang='uz'):
        return getattr(self, f'text_{lang}', None) or self.text_uz


class LessonProgress(models.Model):
    """Foydalanuvchining dars holati."""
    STATUS_LOCKED = 'locked'
    STATUS_WATCHED = 'watched'
    STATUS_PASSED = 'passed'
    STATUS_CHOICES = [
        (STATUS_LOCKED, 'Qulflangan'),
        (STATUS_WATCHED, 'Ko\'rildi'),
        (STATUS_PASSED, 'Topshirildi'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    status = models.CharField(_("holat"), max_length=16, choices=STATUS_CHOICES, default=STATUS_LOCKED)
    last_score = models.PositiveIntegerField(_("oxirgi ball"), null=True, blank=True)
    watched_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'lesson')]
        ordering = ['-updated_at']
        verbose_name = _("Progress")
        verbose_name_plural = _("Progresslar")

    def __str__(self):
        return f'{self.user.username} — {self.lesson.title_uz} ({self.status})'