from django.urls import path

from .views import ConnectionCallbackView, ConnectionDetailView, ConnectionListCreateView

urlpatterns = [
    path("connections", ConnectionListCreateView.as_view(), name="connection-list-create"),
    path("connections/callback", ConnectionCallbackView.as_view(), name="connection-callback"),
    path("connections/<uuid:pk>", ConnectionDetailView.as_view(), name="connection-detail"),
]
