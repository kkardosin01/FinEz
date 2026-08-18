from django.urls import path

from .views import BudgetListUpsertView

urlpatterns = [
    path("budgets", BudgetListUpsertView.as_view(), name="budget-list-upsert"),
]
