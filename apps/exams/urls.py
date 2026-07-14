"""URLs for exams app — config/urls.py da /api/ ostiga ulanadi."""
from django.urls import path

from .views import (
    TestListCreateView,
    TestDetailView,
    MyScoresView,
    ScoresView,
    LeaderboardView,
)

urlpatterns = [
    path('tests/', TestListCreateView.as_view(), name='test-list'),
    path('tests/<int:test_id>/', TestDetailView.as_view(), name='test-detail'),
    path('scores/my/', MyScoresView.as_view(), name='my-scores'),
    path('scores/', ScoresView.as_view(), name='scores'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
