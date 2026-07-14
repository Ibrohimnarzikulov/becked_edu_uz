"""Admin for courses."""
from django.contrib import admin
from .models import Course, Lesson, Test, Question, Choice, LessonProgress


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title_uz', 'type', 'icon', 'order', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('title_uz', 'title_ru', 'title_en', 'slug')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title_uz', 'course', 'order', 'duration', 'youtube_id')
    list_filter = ('course',)
    search_fields = ('title_uz', 'youtube_id')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title_uz', 'lesson', 'subject', 'type')
    search_fields = ('title_uz', 'subject')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_uz', 'test', 'order')
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text_uz', 'question', 'is_correct', 'order')
    list_filter = ('is_correct',)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'status', 'last_score', 'watched_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'lesson__title_uz')