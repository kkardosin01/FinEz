import httpx
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import User
from investments.models import Holding
from investments.pricing import get_crypto_prices, get_current_prices, get_stock_prices

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_cache():
    # cotações são cacheadas por 5min (Redis real, compartilhado entre testes) —
    # limpa antes de cada teste pra não vazar preço mockado de um teste pro outro.
    cache.clear()


@pytest.fixture
def user():
    return User.objects.create_user(email="teste@finez.app", password="senha-forte-123")


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


# --- pricing.py ------------------------------------------------------------------


def test_get_crypto_prices_returns_cents(monkeypatch):
    monkeypatch.setattr(
        httpx, "get", lambda *a, **k: FakeResponse({"bitcoin": {"brl": 350000.5}, "ethereum": {"brl": 12000}})
    )
    prices = get_crypto_prices(["bitcoin", "ethereum"])
    assert prices == {"bitcoin": 35000050, "ethereum": 1200000}


def test_get_crypto_prices_empty_list_is_a_noop(monkeypatch):
    called = []
    monkeypatch.setattr(httpx, "get", lambda *a, **k: called.append(1))
    assert get_crypto_prices([]) == {}
    assert called == []


def test_get_crypto_prices_provider_failure_returns_empty(monkeypatch):
    def raise_error(*a, **k):
        raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(httpx, "get", raise_error)
    assert get_crypto_prices(["bitcoin"]) == {}


def test_get_stock_prices_returns_cents(monkeypatch, settings):
    settings.BRAPI_TOKEN = "fake-token"
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *a, **k: FakeResponse({"results": [{"symbol": "PETR4", "regularMarketPrice": 38.5}]}),
    )
    prices = get_stock_prices(["PETR4"])
    assert prices == {"PETR4": 3850}


def test_get_stock_prices_without_token_returns_empty(monkeypatch, settings):
    settings.BRAPI_TOKEN = ""
    called = []
    monkeypatch.setattr(httpx, "get", lambda *a, **k: called.append(1))
    assert get_stock_prices(["PETR4"]) == {}
    assert called == []


def test_get_current_prices_combines_crypto_and_stocks(monkeypatch, settings, user):
    settings.BRAPI_TOKEN = "fake-token"

    def fake_get(url, **kwargs):
        if "coingecko" in url:
            return FakeResponse({"bitcoin": {"brl": 350000}})
        return FakeResponse({"results": [{"symbol": "PETR4", "regularMarketPrice": 38.5}]})

    monkeypatch.setattr(httpx, "get", fake_get)

    holdings = [
        Holding(user=user, kind=Holding.Kind.CRYPTO, symbol="bitcoin", quantity=1, avg_price_cents=30000000),
        Holding(user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3500),
    ]
    prices = get_current_prices(holdings)
    assert prices[("crypto", "bitcoin")] == 35000000
    assert prices[("stock", "PETR4")] == 3850


# --- Holding CRUD ------------------------------------------------------------------


def test_holdings_requires_authentication():
    response = APIClient().get("/api/investments/holdings")
    assert response.status_code in (401, 403)


def test_create_holding(client):
    response = client.post(
        "/api/investments/holdings",
        {"kind": "stock", "symbol": "PETR4", "name": "Petrobras", "quantity": "10", "avg_price_cents": 3500},
        format="json",
    )
    assert response.status_code == 201
    assert Holding.objects.count() == 1


def test_create_holding_rejects_zero_quantity(client):
    response = client.post(
        "/api/investments/holdings",
        {"kind": "stock", "symbol": "PETR4", "quantity": "0", "avg_price_cents": 3500},
        format="json",
    )
    assert response.status_code == 400


def test_list_holdings_only_returns_own(client, user):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    Holding.objects.create(user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3500)
    Holding.objects.create(user=other_user, kind=Holding.Kind.STOCK, symbol="VALE3", quantity=5, avg_price_cents=7000)

    response = client.get("/api/investments/holdings")
    assert response.status_code == 200
    assert [h["symbol"] for h in response.data] == ["PETR4"]


def test_delete_holding(client, user):
    holding = Holding.objects.create(
        user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3500
    )
    response = client.delete(f"/api/investments/holdings/{holding.id}")
    assert response.status_code == 204
    assert not Holding.objects.filter(id=holding.id).exists()


def test_cannot_access_another_users_holding(client):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    holding = Holding.objects.create(
        user=other_user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3500
    )
    response = client.get(f"/api/investments/holdings/{holding.id}")
    assert response.status_code == 404


# --- buy / sell ------------------------------------------------------------------


def test_buy_recalculates_weighted_average_price(client, user):
    holding = Holding.objects.create(
        user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3000
    )
    response = client.post(f"/api/investments/holdings/{holding.id}/buy", {"quantity": "10", "price_cents": 4000})
    assert response.status_code == 200
    holding.refresh_from_db()
    assert holding.quantity == 20
    assert holding.avg_price_cents == 3500  # média ponderada: (10*3000 + 10*4000) / 20


def test_sell_reduces_quantity_without_changing_avg_price(client, user):
    holding = Holding.objects.create(
        user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3000
    )
    response = client.post(f"/api/investments/holdings/{holding.id}/sell", {"quantity": "4"})
    assert response.status_code == 200
    holding.refresh_from_db()
    assert holding.quantity == 6
    assert holding.avg_price_cents == 3000


def test_sell_full_position_deletes_holding(client, user):
    holding = Holding.objects.create(
        user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3000
    )
    response = client.post(f"/api/investments/holdings/{holding.id}/sell", {"quantity": "10"})
    assert response.status_code == 204
    assert not Holding.objects.filter(id=holding.id).exists()


def test_sell_more_than_owned_is_rejected(client, user):
    holding = Holding.objects.create(
        user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3000
    )
    response = client.post(f"/api/investments/holdings/{holding.id}/sell", {"quantity": "11"})
    assert response.status_code == 400
    holding.refresh_from_db()
    assert holding.quantity == 10


# --- portfolio summary ------------------------------------------------------------


def test_portfolio_summary_computes_gain_and_totals(client, user, monkeypatch, settings):
    settings.BRAPI_TOKEN = "fake-token"
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *a, **k: FakeResponse({"results": [{"symbol": "PETR4", "regularMarketPrice": 40}]}),
    )
    Holding.objects.create(user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3000)

    response = client.get("/api/investments/portfolio")
    assert response.status_code == 200
    row = response.data["holdings"][0]
    assert row["invested_cents"] == 30000
    assert row["current_value_cents"] == 40000
    assert row["gain_cents"] == 10000
    assert response.data["total_invested_cents"] == 30000
    assert response.data["total_current_cents"] == 40000
    assert response.data["total_gain_cents"] == 10000


def test_portfolio_summary_totals_are_null_when_a_price_is_missing(client, user, monkeypatch, settings):
    settings.BRAPI_TOKEN = ""  # sem token -> preço de ações não resolve
    Holding.objects.create(user=user, kind=Holding.Kind.STOCK, symbol="PETR4", quantity=10, avg_price_cents=3000)

    response = client.get("/api/investments/portfolio")
    assert response.status_code == 200
    row = response.data["holdings"][0]
    assert row["current_value_cents"] is None
    assert response.data["total_current_cents"] is None
    assert response.data["total_gain_cents"] is None


def test_portfolio_summary_empty_holdings(client):
    response = client.get("/api/investments/portfolio")
    assert response.status_code == 200
    assert response.data["holdings"] == []
    assert response.data["total_invested_cents"] == 0


# --- top movers (comportamento pré-existente) --------------------------------------


def test_top_movers_returns_crypto_and_stocks(client, monkeypatch, settings):
    settings.BRAPI_TOKEN = "fake-token"

    def fake_get(url, **kwargs):
        if "coingecko" in url:
            return FakeResponse(
                [{"symbol": "btc", "name": "Bitcoin", "current_price": 350000, "price_change_percentage_24h": 5.5}]
            )
        return FakeResponse(
            {
                "results": [
                    {
                        "symbol": "PETR4",
                        "longName": "Petrobras",
                        "regularMarketPrice": 38.5,
                        "regularMarketChangePercent": 2.1,
                    }
                ]
            }
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client.get("/api/investments/top-movers")
    assert response.status_code == 200
    assert response.data["crypto"][0]["symbol"] == "BTC"
    assert response.data["stocks_and_fiis"][0]["symbol"] == "PETR4"


def test_top_movers_without_brapi_token_returns_empty_stocks(client, monkeypatch, settings):
    settings.BRAPI_TOKEN = ""
    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse([]))

    response = client.get("/api/investments/top-movers")
    assert response.status_code == 200
    assert response.data["stocks_and_fiis"] == []


def test_top_movers_provider_failure_returns_empty_lists(client, monkeypatch):
    def raise_error(*a, **k):
        raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(httpx, "get", raise_error)

    response = client.get("/api/investments/top-movers")
    assert response.status_code == 200
    assert response.data["crypto"] == []
    assert response.data["stocks_and_fiis"] == []
