from django.urls import path

from .webhook_views import pluggy_webhook

urlpatterns = [
    path("aggregator", pluggy_webhook, name="pluggy-webhook"),
]
