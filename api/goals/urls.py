from django.urls import path

from .views import GoalContributeView, GoalContributionListView, GoalDetailView, GoalListCreateView

urlpatterns = [
    path("goals", GoalListCreateView.as_view(), name="goal-list-create"),
    path("goals/<uuid:pk>", GoalDetailView.as_view(), name="goal-detail"),
    path("goals/<uuid:pk>/contribute", GoalContributeView.as_view(), name="goal-contribute"),
    path("goals/<uuid:pk>/contributions", GoalContributionListView.as_view(), name="goal-contributions"),
]
