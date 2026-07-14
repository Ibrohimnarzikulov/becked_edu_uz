"""Admin for exams app."""
from django.contrib import admin

from .models import Test, Score


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'subject', 'type', 'created_by', 'created_at')
    list_filter = ('type',)
    search_fields = ('title', 'subject')


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'test', 'score', 'updated_at')
    list_filter = ('test__type',)
    search_fields = ('user__username', 'test__title')
