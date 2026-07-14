"""Admin for school app."""
from django.contrib import admin

from .models import Subject, Assignment, Circle


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 1


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'icon', 'progress', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    inlines = [AssignmentInline]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'subject', 'status', 'order')
    list_filter = ('status', 'subject')
    search_fields = ('title',)


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'icon', 'members', 'schedule', 'order', 'is_active')
    list_editable = ('order', 'is_active')
