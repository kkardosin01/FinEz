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
from rest_framework.response import Response
from rest_framework.views import APIView

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
