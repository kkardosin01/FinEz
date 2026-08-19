from django.urls import path

from .views import InvestmentsTopMoversView

urlpatterns = [
    path("investments/top-movers", InvestmentsTopMoversView.as_view(), name="investments-top-movers"),
]
