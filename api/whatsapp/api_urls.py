from django.urls import path

from .views import PairView

urlpatterns = [
    path("pair", PairView.as_view(), name="whatsapp-pair"),
]
