from django.urls import path

from .webhook_views import whatsapp_webhook

urlpatterns = [
    path("whatsapp", whatsapp_webhook, name="whatsapp-webhook"),
]
