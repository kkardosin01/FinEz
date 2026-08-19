"""Cotação atual de posições da carteira (distinto do `views.py` de "maiores
altas", que busca listas curadas/top do mercado). Aqui a busca é por símbolo
específico, sob demanda, pros tickers que o usuário efetivamente tem."""
import httpx
from django.conf import settings
from django.core.cache import cache

CACHE_TTL = 60 * 5  # 5min — mesmo TTL do resto do módulo, evita rate limit


def get_crypto_prices(coingecko_ids: list[str]) -> dict[str, int]:
    """id da CoinGecko -> preço atual em centavos (BRL)."""
    if not coingecko_ids:
        return {}
    cache_key = f"investments:crypto:price:{','.join(sorted(coingecko_ids))}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        resp = httpx.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ",".join(coingecko_ids), "vs_currencies": "brl"},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return {}

    prices = {coin_id: round(info["brl"] * 100) for coin_id, info in data.items() if "brl" in info}
    cache.set(cache_key, prices, CACHE_TTL)
    return prices


def get_stock_prices(tickers: list[str]) -> dict[str, int]:
    """ticker (ação/FII) -> preço atual em centavos (BRL). Requer BRAPI_TOKEN."""
    if not tickers or not settings.BRAPI_TOKEN:
        return {}
    cache_key = f"investments:stock:price:{','.join(sorted(tickers))}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        resp = httpx.get(
            f"https://brapi.dev/api/quote/{','.join(tickers)}",
            params={"token": settings.BRAPI_TOKEN},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return {}

    prices = {
        row["symbol"]: round(row["regularMarketPrice"] * 100)
        for row in data.get("results", [])
        if row.get("regularMarketPrice") is not None
    }
    cache.set(cache_key, prices, CACHE_TTL)
    return prices


def get_current_prices(holdings) -> dict[tuple[str, str], int]:
    """(kind, symbol) -> preço atual em centavos, pra um conjunto de holdings."""
    crypto_symbols = {h.symbol for h in holdings if h.kind == "crypto"}
    stock_symbols = {h.symbol for h in holdings if h.kind in ("stock", "fii")}

    crypto_prices = get_crypto_prices(list(crypto_symbols))
    stock_prices = get_stock_prices(list(stock_symbols))

    result: dict[tuple[str, str], int] = {}
    for symbol, price in crypto_prices.items():
        result[("crypto", symbol)] = price
    for symbol, price in stock_prices.items():
        result[("stock", symbol)] = price
        result[("fii", symbol)] = price
    return result
