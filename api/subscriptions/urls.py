from django.urls import path

from .views import SubscriptionDetailView, SubscriptionListView

urlpatterns = [
    path("subscriptions", SubscriptionListView.as_view(), name="subscription-list"),
    path("subscriptions/<uuid:pk>", SubscriptionDetailView.as_view(), name="subscription-detail"),
]
