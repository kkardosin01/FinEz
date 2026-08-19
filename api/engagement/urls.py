from django.urls import path

from .views import GamificationSummaryView

urlpatterns = [
    path("engagement/summary", GamificationSummaryView.as_view()),
]
