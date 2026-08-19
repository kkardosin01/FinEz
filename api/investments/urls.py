from django.urls import path

from .views import (
    HoldingBuyView,
    HoldingDetailView,
    HoldingListCreateView,
    HoldingSellView,
    InvestmentsTopMoversView,
    PortfolioSummaryView,
)

urlpatterns = [
    path("investments/top-movers", InvestmentsTopMoversView.as_view(), name="investments-top-movers"),
    path("investments/portfolio", PortfolioSummaryView.as_view(), name="investments-portfolio"),
    path("investments/holdings", HoldingListCreateView.as_view(), name="holding-list-create"),
    path("investments/holdings/<uuid:pk>", HoldingDetailView.as_view(), name="holding-detail"),
    path("investments/holdings/<uuid:pk>/buy", HoldingBuyView.as_view(), name="holding-buy"),
    path("investments/holdings/<uuid:pk>/sell", HoldingSellView.as_view(), name="holding-sell"),
]
