"""Maiores altas do dia (cripto + ações/FIIs) — provedores públicos e gratuitos.

CoinGecko pra cripto (sem chave). brapi.dev pra ações/FIIs (conjunto curado
de tickers, já que o plano gratuito não expõe "top movers") — exige
BRAPI_TOKEN configurado; sem ele, a lista de ações/FIIs vem vazia.
Falha de qualquer provedor não derruba a resposta — devolve lista vazia pro
grupo afetado.
"""
import httpx
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Holding
from .pricing import get_current_prices
from .serializers import HoldingBuySerializer, HoldingSellSerializer, HoldingSerializer

CRYPTO_CACHE_KEY = "investments:crypto:top"
STOCKS_CACHE_KEY = "investments:stocks:top"
CACHE_TTL = 60 * 5  # 5min — evita estourar rate limit dos provedores públicos

STOCK_TICKERS = ["PETR4", "VALE3", "ITUB4", "BBDC4", "MXRF11", "HGLG11", "KNRI11", "XPML11"]


def _fetch_crypto_top_movers():
    cached = cache.get(CRYPTO_CACHE_KEY)
    if cached is not None:
        return cached
    try:
        resp = httpx.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "brl",
                "order": "market_cap_desc",
                "per_page": 50,
                "page": 1,
                "price_change_percentage": "24h",
            },
            timeout=5.0,
        )
        resp.raise_for_status()
        coins = resp.json()
    except (httpx.HTTPError, ValueError):
        return []

    movers = [
        {
            "symbol": coin["symbol"].upper(),
            "name": coin["name"],
            "price": coin["current_price"],
            "change_pct": coin["price_change_percentage_24h"],
            "kind": "crypto",
        }
        for coin in coins
        if coin.get("price_change_percentage_24h") is not None
    ]
    movers.sort(key=lambda m: m["change_pct"], reverse=True)
    top = movers[:5]
    cache.set(CRYPTO_CACHE_KEY, top, CACHE_TTL)
    return top


def _fetch_stock_top_movers():
    cached = cache.get(STOCKS_CACHE_KEY)
    if cached is not None:
        return cached
    if not settings.BRAPI_TOKEN:
        return []
    try:
        resp = httpx.get(
            f"https://brapi.dev/api/quote/{','.join(STOCK_TICKERS)}",
            params={"token": settings.BRAPI_TOKEN},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return []

    movers = [
        {
            "symbol": row["symbol"],
            "name": row.get("longName") or row["symbol"],
            "price": row.get("regularMarketPrice"),
            "change_pct": row["regularMarketChangePercent"],
            "kind": "fii" if row["symbol"].endswith("11") else "stock",
        }
        for row in data.get("results", [])
        if row.get("regularMarketChangePercent") is not None
    ]
    movers.sort(key=lambda m: m["change_pct"], reverse=True)
    top = movers[:5]
    cache.set(STOCKS_CACHE_KEY, top, CACHE_TTL)
    return top


class InvestmentsTopMoversView(APIView):
    """GET /api/investments/top-movers — maiores altas do dia."""

    def get(self, request):
        return Response(
            {
                "crypto": _fetch_crypto_top_movers(),
                "stocks_and_fiis": _fetch_stock_top_movers(),
            }
        )


class HoldingListCreateView(generics.ListCreateAPIView):
    """Carteira do usuário (seção 3 — deep-dive de investimentos)."""

    serializer_class = HoldingSerializer
    pagination_class = None

    def get_queryset(self):
        return Holding.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HoldingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HoldingSerializer

    def get_queryset(self):
        return Holding.objects.filter(user=self.request.user)


class HoldingBuyView(APIView):
    """POST /api/investments/holdings/<id>/buy — soma quantidade e recalcula o preço médio."""

    def post(self, request, pk):
        holding = get_object_or_404(Holding, pk=pk, user=request.user)
        serializer = HoldingBuySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        price_cents = serializer.validated_data["price_cents"]

        new_quantity = holding.quantity + quantity
        new_avg_price_cents = round(
            (holding.quantity * holding.avg_price_cents + quantity * price_cents) / new_quantity
        )

        holding.quantity = new_quantity
        holding.avg_price_cents = new_avg_price_cents
        holding.save(update_fields=["quantity", "avg_price_cents", "updated_at"])

        return Response(HoldingSerializer(holding).data)


class HoldingSellView(APIView):
    """POST /api/investments/holdings/<id>/sell — reduz quantidade (custo médio não muda);
    zerar a posição remove a holding."""

    def post(self, request, pk):
        holding = get_object_or_404(Holding, pk=pk, user=request.user)
        serializer = HoldingSellSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]

        new_quantity = holding.quantity - quantity
        if new_quantity < 0:
            return Response(
                {"quantity": "venda maior que a quantidade que você tem"}, status=status.HTTP_400_BAD_REQUEST
            )

        if new_quantity == 0:
            holding.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        holding.quantity = new_quantity
        holding.save(update_fields=["quantity", "updated_at"])
        return Response(HoldingSerializer(holding).data)


class PortfolioSummaryView(APIView):
    """GET /api/investments/portfolio — carteira com cotação atual e ganho/perda."""

    def get(self, request):
        holdings = list(Holding.objects.filter(user=request.user))
        prices = get_current_prices(holdings)

        rows = []
        total_invested_cents = 0
        total_current_cents = 0
        for holding in holdings:
            invested_cents = round(holding.quantity * holding.avg_price_cents)
            total_invested_cents += invested_cents

            current_price_cents = prices.get((holding.kind, holding.symbol))
            current_value_cents = round(holding.quantity * current_price_cents) if current_price_cents else None
            if current_value_cents is not None:
                total_current_cents += current_value_cents

            rows.append(
                {
                    "id": str(holding.id),
                    "kind": holding.kind,
                    "symbol": holding.symbol,
                    "name": holding.name,
                    "quantity": str(holding.quantity),
                    "avg_price_cents": holding.avg_price_cents,
                    "invested_cents": invested_cents,
                    "current_price_cents": current_price_cents,
                    "current_value_cents": current_value_cents,
                    "gain_cents": (current_value_cents - invested_cents) if current_value_cents is not None else None,
                    "gain_pct": (
                        round((current_value_cents - invested_cents) / invested_cents * 100, 2)
                        if current_value_cents is not None and invested_cents
                        else None
                    ),
                }
            )

        has_missing_prices = any(row["current_value_cents"] is None for row in rows)
        return Response(
            {
                "holdings": rows,
                "total_invested_cents": total_invested_cents,
                "total_current_cents": total_current_cents if not has_missing_prices else None,
                "total_gain_cents": (
                    total_current_cents - total_invested_cents if not has_missing_prices else None
                ),
            }
        )
