"""URLs for school app."""
from django.urls import path

from .views import (
    SubjectListView,
    AssignmentListView,
    CircleListView,
    SchoolTestListView,
)

urlpatterns = [
    path('subjects/', SubjectListView.as_view(), name='school-subjects'),
    path('assignments/', AssignmentListView.as_view(), name='school-assignments'),
    path('circles/', CircleListView.as_view(), name='school-circles'),
    path('tests/', SchoolTestListView.as_view(), name='school-tests'),
]
