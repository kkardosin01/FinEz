from datetime import date

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from budgets.models import Budget
from budgets.tasks import check_budget_alerts
from transactions.models import Account, Category, Transaction
from whatsapp.models import WhatsappLink

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
        for slug in [Category.Slug.FOOD, Category.Slug.GROCERIES]
    }


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


def test_budgets_requires_authentication():
    response = APIClient().get("/api/budgets")
    assert response.status_code in (401, 403)


def test_get_budgets_computes_spent_from_expenses_only(client, user, account, categories):
    Budget.objects.create(user=user, category=categories[Category.Slug.FOOD], amount_cents=20000, month=date(2026, 8, 1))
    Transaction.objects.create(
        user=user, account=account, category=categories[Category.Slug.FOOD], amount_cents=-5000,
        description="lanche", date=date(2026, 8, 5),
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )
    # receita na mesma categoria não deve contar como gasto
    Transaction.objects.create(
        user=user, account=account, category=categories[Category.Slug.FOOD], amount_cents=3000,
        description="reembolso", date=date(2026, 8, 6),
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )

    response = client.get("/api/budgets?month=2026-08")
    assert response.status_code == 200
    assert response.data[0]["spent_cents"] == 5000


def test_get_budgets_ignores_transactions_outside_month(client, user, account, categories):
    Budget.objects.create(user=user, category=categories[Category.Slug.FOOD], amount_cents=20000, month=date(2026, 8, 1))
    Transaction.objects.create(
        user=user, account=account, category=categories[Category.Slug.FOOD], amount_cents=-9000,
        description="lanche mes anterior", date=date(2026, 7, 30),
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )

    response = client.get("/api/budgets?month=2026-08")
    assert response.status_code == 200
    assert response.data[0]["spent_cents"] == 0


def test_put_budgets_creates_and_updates(client, user, categories):
    response = client.put(
        "/api/budgets",
        {
            "month": "2026-08-01",
            "budgets": [{"category": categories[Category.Slug.FOOD].id, "amount_cents": 30000}],
        },
        format="json",
    )
    assert response.status_code == 200
    assert Budget.objects.count() == 1
    assert Budget.objects.get().amount_cents == 30000

    # upsert: mesmo user/categoria/mês atualiza em vez de duplicar
    response = client.put(
        "/api/budgets",
        {
            "month": "2026-08-15",  # mesmo mês, dia diferente — deve normalizar pro dia 1
            "budgets": [{"category": categories[Category.Slug.FOOD].id, "amount_cents": 45000}],
        },
        format="json",
    )
    assert response.status_code == 200
    assert Budget.objects.count() == 1
    budget = Budget.objects.get()
    assert budget.amount_cents == 45000
    assert budget.month == date(2026, 8, 1)


def test_cannot_see_another_users_budgets(client, user, categories):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    Budget.objects.create(user=other_user, category=categories[Category.Slug.FOOD], amount_cents=10000, month=date(2026, 8, 1))

    response = client.get("/api/budgets?month=2026-08")
    assert response.status_code == 200
    assert response.data == []


# --- check_budget_alerts task -----------------------------------------------


def _month_start():
    today = date.today()
    return date(today.year, today.month, 1)


def test_check_budget_alerts_triggers_80_percent_once(user, account, categories, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    budget = Budget.objects.create(
        user=user, category=categories[Category.Slug.FOOD], amount_cents=10000, month=_month_start()
    )
    Transaction.objects.create(
        user=user, account=account, category=categories[Category.Slug.FOOD], amount_cents=-8000,
        description="lanche", date=date.today(),
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )

    check_budget_alerts(str(user.id))

    budget.refresh_from_db()
    assert budget.alerted_80_at is not None
    assert budget.alerted_100_at is None
    assert len(sent) == 1
    assert "80%" in sent[0]

    # nova chamada não deve reenviar o mesmo alerta
    check_budget_alerts(str(user.id))
    assert len(sent) == 1


def test_check_budget_alerts_triggers_100_percent(user, account, categories, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    budget = Budget.objects.create(
        user=user, category=categories[Category.Slug.FOOD], amount_cents=10000, month=_month_start()
    )
    Transaction.objects.create(
        user=user, account=account, category=categories[Category.Slug.FOOD], amount_cents=-15000,
        description="lanche caro", date=date.today(),
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )

    check_budget_alerts(str(user.id))

    budget.refresh_from_db()
    assert budget.alerted_100_at is not None
    assert "estourou" in sent[0]


def test_check_budget_alerts_below_threshold_does_not_alert(user, account, categories, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    budget = Budget.objects.create(
        user=user, category=categories[Category.Slug.FOOD], amount_cents=10000, month=_month_start()
    )
    Transaction.objects.create(
        user=user, account=account, category=categories[Category.Slug.FOOD], amount_cents=-2000,
        description="lanche", date=date.today(),
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )

    check_budget_alerts(str(user.id))

    budget.refresh_from_db()
    assert budget.alerted_80_at is None
    assert sent == []


def test_check_budget_alerts_without_whatsapp_link_still_marks_alert(user, account, categories, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    budget = Budget.objects.create(
        user=user, category=categories[Category.Slug.FOOD], amount_cents=10000, month=_month_start()
    )
    Transaction.objects.create(
        user=user, account=account, category=categories[Category.Slug.FOOD], amount_cents=-9000,
        description="lanche", date=date.today(),
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )

    check_budget_alerts(str(user.id))

    budget.refresh_from_db()
    assert budget.alerted_80_at is not None
    assert sent == []  # sem link ativo, não envia — mas o alerta fica marcado


def test_check_budget_alerts_unknown_user_is_a_noop():
    check_budget_alerts("00000000-0000-0000-0000-000000000000")
