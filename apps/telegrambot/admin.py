from django.contrib import admin

from .models import TelegramLink


@admin.register(TelegramLink)
class TelegramLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_id', 'linked_at')
    search_fields = ('user__username', 'user__full_name')
    readonly_fields = ('linked_at',)
