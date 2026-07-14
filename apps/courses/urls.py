"""URLs for courses app."""
from django.urls import path

from .views import (
    CourseListView,
    DailyLimitView,
    WatchLessonView,
    LessonTestView,
    SubmitTestView,
    AdminLessonTestView,
    AdminCourseListView,
    AdminLessonProgressListView,
)

urlpatterns = [
    path('', CourseListView.as_view(), name='course-list'),
    path('daily-limit/', DailyLimitView.as_view(), name='daily-limit'),
    path('lessons/<int:lesson_id>/watch/', WatchLessonView.as_view(), name='watch-lesson'),
    path('lessons/<int:lesson_id>/test/', LessonTestView.as_view(), name='lesson-test'),
    path('lessons/<int:lesson_id>/test/submit/', SubmitTestView.as_view(), name='submit-test'),
    path('admin/', AdminCourseListView.as_view(), name='admin-course-list'),
    path('admin/progress/', AdminLessonProgressListView.as_view(), name='admin-progress-list'),
    path('admin/lessons/<int:lesson_id>/test/', AdminLessonTestView.as_view(), name='admin-lesson-test'),
]
