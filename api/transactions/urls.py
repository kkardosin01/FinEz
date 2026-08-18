from django.urls import path

from .views import CategoryListView, SummaryView, TransactionDetailView, TransactionListCreateView

urlpatterns = [
    path("categories", CategoryListView.as_view(), name="category-list"),
    path("transactions", TransactionListCreateView.as_view(), name="transaction-list-create"),
    path("transactions/<uuid:pk>", TransactionDetailView.as_view(), name="transaction-detail"),
    path("summary", SummaryView.as_view(), name="summary"),
]
