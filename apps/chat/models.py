"""Models for chat app — oddiy 1:1 suhbat va xabarlar."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Conversation(models.Model):
    """Ikki foydalanuvchi orasidagi suhbat."""
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_a'
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_b'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Bir juftlik uchun bitta suhbat (user_a < user_b tartibida saqlanadi)
        unique_together = [('user_a', 'user_b')]
        ordering = ['-updated_at']
        verbose_name = _("Suhbat")
        verbose_name_plural = _("Suhbatlar")

    def __str__(self):
        return f'{self.user_a.username} ↔ {self.user_b.username}'

    def partner_for(self, user):
        """Berilgan foydalanuvchi uchun suhbatdoshni qaytaradi."""
        return self.user_b if self.user_a_id == user.id else self.user_a

    @classmethod
    def between(cls, u1, u2):
        """Ikki foydalanuvchi orasidagi suhbatni oladi yoki yaratadi (tartib barqaror)."""
        a, b = (u1, u2) if u1.id < u2.id else (u2, u1)
        conv, _created = cls.objects.get_or_create(user_a=a, user_b=b)
        return conv


class Message(models.Model):
    """Suhbatdagi bitta xabar."""
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    text = models.TextField(_("matn"))
    is_read = models.BooleanField(_("o'qilgan"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        verbose_name = _("Xabar")
        verbose_name_plural = _("Xabarlar")

    def __str__(self):
        return f'{self.sender.username}: {self.text[:40]}'
