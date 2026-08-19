from datetime import date

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from transactions.models import Account, Category, Transaction

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="teste@finez.app", password="senha-forte-123")


@pytest.fixture
def account(user):
    return Account.objects.create(user=user, type=Account.Type.MANUAL, name="Manual")


@pytest.fixture
def categories():
    return {
        slug: Category.objects.create(slug=slug, name_pt=slug, color_light="#000000", color_dark="#ffffff")
        for slug in [Category.Slug.FOOD, Category.Slug.LEISURE, Category.Slug.GROCERIES]
    }


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


def _make_transaction(user, account, category, amount_cents, day, description="lançamento"):
    return Transaction.objects.create(
        user=user,
        account=account,
        category=category,
        amount_cents=amount_cents,
        description=description,
        date=day,
        category_source=Transaction.CategorySource.USER,
        origin=Transaction.Origin.WEB,
    )


def test_no_transactions_in_month_returns_zeroed_data_with_fallback_message(client):
    response = client.get("/api/insights?month=2026-08")
    assert response.status_code == 200
    assert response.data["total_expense_cents"] == 0
    assert response.data["top_categories"] == []
    assert response.data["biggest_single_transaction"] is None
    assert response.data["messages"] == ["Sem dados suficientes ainda pra gerar insights esse mês."]


def test_empty_previous_month_does_not_divide_by_zero(client, user, account, categories):
    _make_transaction(user, account, categories[Category.Slug.FOOD], -10000, date(2026, 8, 5))

    response = client.get("/api/insights?month=2026-08")
    assert response.status_code == 200
    assert response.data["total_expense_change_pct"] is None
    assert response.data["top_categories"][0]["change_pct_vs_prev_month"] is None


def test_new_category_without_history_is_not_flagged_as_biggest_increase(client, user, account, categories):
    # mês anterior: só mercado
    _make_transaction(user, account, categories[Category.Slug.GROCERIES], -20000, date(2026, 7, 10))
    # mês atual: mercado estável + categoria nova (lazer) sem histórico
    _make_transaction(user, account, categories[Category.Slug.GROCERIES], -20000, date(2026, 8, 10))
    _make_transaction(user, account, categories[Category.Slug.LEISURE], -5000, date(2026, 8, 12))

    response = client.get("/api/insights?month=2026-08")
    assert response.status_code == 200
    leisure_row = next(c for c in response.data["top_categories"] if c["category_slug"] == "leisure")
    assert leisure_row["change_pct_vs_prev_month"] is None
    # categoria nova sem histórico nunca deve ser eleita "maior aumento"
    increase = response.data["biggest_increase_category"]
    assert increase is None or increase["category_name"] != "leisure"


def test_biggest_single_transaction_dominates_correctly(client, user, account, categories):
    _make_transaction(user, account, categories[Category.Slug.FOOD], -1500, date(2026, 8, 3), "lanche")
    _make_transaction(user, account, categories[Category.Slug.LEISURE], -50000, date(2026, 8, 18), "tenis")

    response = client.get("/api/insights?month=2026-08")
    assert response.status_code == 200
    biggest = response.data["biggest_single_transaction"]
    assert biggest["description"] == "tenis"
    assert biggest["amount_cents"] == -50000
    assert any("tenis" in message for message in response.data["messages"])


def test_insights_requires_authentication():
    response = APIClient().get("/api/insights")
    assert response.status_code in (401, 403)
