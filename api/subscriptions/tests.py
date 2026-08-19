from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from subscriptions.detection import find_recurring_candidates, normalize_description
from subscriptions.models import Subscription
from subscriptions.tasks import detect_subscriptions
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
def category():
    return Category.objects.create(
        slug=Category.Slug.LEISURE, name_pt="Lazer", color_light="#000000", color_dark="#ffffff"
    )


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


def _tx(user, account, category, amount_cents, day, description):
    return Transaction.objects.create(
        user=user, account=account, category=category, amount_cents=amount_cents,
        description=description, date=day,
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )


# --- normalize_description / find_recurring_candidates -----------------------


def test_normalize_description_strips_numbers_and_extra_spaces():
    assert normalize_description("Netflix.com  123456") == "netflix.com"
    assert normalize_description("SPOTIFY   AB") == "spotify ab"


def test_find_recurring_candidates_detects_monthly_cadence(user, account, category):
    _tx(user, account, category, -3990, date.today() - timedelta(days=60), "Netflix.com")
    _tx(user, account, category, -3990, date.today() - timedelta(days=30), "Netflix.com")
    _tx(user, account, category, -3990, date.today(), "Netflix.com")

    candidates = find_recurring_candidates(user)
    assert len(candidates) == 1
    key, txs = candidates[0]
    assert key == "netflix.com"
    assert len(txs) == 3


def test_find_recurring_candidates_ignores_single_occurrence(user, account, category):
    _tx(user, account, category, -5000, date.today(), "Compra única")
    assert find_recurring_candidates(user) == []


def test_find_recurring_candidates_ignores_same_month_repeats(user, account, category):
    # duas compras na mesma semana não formam cadência mensal
    _tx(user, account, category, -1500, date.today() - timedelta(days=1), "Ifood")
    _tx(user, account, category, -1500, date.today(), "Ifood")
    assert find_recurring_candidates(user) == []


def test_find_recurring_candidates_ignores_income(user, account, category):
    _tx(user, account, category, 3990, date.today() - timedelta(days=30), "Salario")
    _tx(user, account, category, 3990, date.today(), "Salario")
    assert find_recurring_candidates(user) == []


# --- detect_subscriptions task ------------------------------------------------


def test_detect_subscriptions_creates_subscription(user, account, category):
    _tx(user, account, category, -3990, date.today() - timedelta(days=30), "Netflix.com")
    _tx(user, account, category, -3990, date.today(), "Netflix.com")

    detect_subscriptions(str(user.id))

    subscription = Subscription.objects.get(user=user)
    assert subscription.name == "Netflix.com"
    assert subscription.amount_cents == 3990
    assert subscription.status == Subscription.Status.ACTIVE


def test_detect_subscriptions_is_idempotent_across_runs(user, account, category):
    _tx(user, account, category, -3990, date.today() - timedelta(days=30), "Netflix.com")
    _tx(user, account, category, -3990, date.today(), "Netflix.com")

    detect_subscriptions(str(user.id))
    detect_subscriptions(str(user.id))

    assert Subscription.objects.filter(user=user).count() == 1


def test_detect_subscriptions_price_increase_updates_amount_and_notifies(user, account, category, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    _tx(user, account, category, -3990, date.today() - timedelta(days=30), "Netflix.com")
    _tx(user, account, category, -3990, date.today(), "Netflix.com")
    detect_subscriptions(str(user.id))

    # mês seguinte, preço subiu
    _tx(user, account, category, -4490, date.today() + timedelta(days=30), "Netflix.com")
    detect_subscriptions(str(user.id))

    subscription = Subscription.objects.get(user=user)
    assert subscription.amount_cents == 4490
    assert subscription.previous_amount_cents == 3990
    assert len(sent) == 1
    assert "mais cara" in sent[0]


def test_detect_subscriptions_price_decrease_updates_silently_without_notifying(user, account, category, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    _tx(user, account, category, -4490, date.today() - timedelta(days=30), "Netflix.com")
    _tx(user, account, category, -4490, date.today(), "Netflix.com")
    detect_subscriptions(str(user.id))

    _tx(user, account, category, -3990, date.today() + timedelta(days=30), "Netflix.com")
    detect_subscriptions(str(user.id))

    subscription = Subscription.objects.get(user=user)
    assert subscription.amount_cents == 3990
    assert sent == []


def test_detect_subscriptions_skips_canceled_subscriptions(user, account, category):
    _tx(user, account, category, -3990, date.today() - timedelta(days=30), "Netflix.com")
    _tx(user, account, category, -3990, date.today(), "Netflix.com")
    detect_subscriptions(str(user.id))

    subscription = Subscription.objects.get(user=user)
    subscription.status = Subscription.Status.CANCELED
    subscription.save(update_fields=["status"])

    _tx(user, account, category, -4490, date.today() + timedelta(days=30), "Netflix.com")
    detect_subscriptions(str(user.id))

    subscription.refresh_from_db()
    assert subscription.amount_cents == 3990  # não atualiza assinatura cancelada
    assert subscription.status == Subscription.Status.CANCELED


def test_detect_subscriptions_unknown_user_is_a_noop():
    detect_subscriptions("00000000-0000-0000-0000-000000000000")


# --- API views -----------------------------------------------------------------


def test_subscriptions_requires_authentication():
    response = APIClient().get("/api/subscriptions")
    assert response.status_code in (401, 403)


def test_list_subscriptions_only_returns_own(client, user, category):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    Subscription.objects.create(
        user=user, name="Netflix", merchant_key="netflix", amount_cents=3990, last_charged_at=date.today()
    )
    Subscription.objects.create(
        user=other_user, name="Spotify", merchant_key="spotify", amount_cents=1990, last_charged_at=date.today()
    )

    response = client.get("/api/subscriptions")
    assert response.status_code == 200
    assert [s["name"] for s in response.data] == ["Netflix"]


def test_update_subscription_name_and_status(client, user):
    subscription = Subscription.objects.create(
        user=user, name="Netflix", merchant_key="netflix", amount_cents=3990, last_charged_at=date.today()
    )
    response = client.patch(
        f"/api/subscriptions/{subscription.id}", {"name": "Netflix Premium", "status": "canceled"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["name"] == "Netflix Premium"
    assert response.data["status"] == "canceled"


def test_cannot_update_another_users_subscription(client):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    subscription = Subscription.objects.create(
        user=other_user, name="Netflix", merchant_key="netflix", amount_cents=3990, last_charged_at=date.today()
    )
    response = client.patch(f"/api/subscriptions/{subscription.id}", {"name": "hack"}, format="json")
    assert response.status_code == 404


def test_amount_cents_is_read_only_via_api(client, user):
    subscription = Subscription.objects.create(
        user=user, name="Netflix", merchant_key="netflix", amount_cents=3990, last_charged_at=date.today()
    )
    response = client.patch(f"/api/subscriptions/{subscription.id}", {"amount_cents": 999999}, format="json")
    assert response.status_code == 200
    subscription.refresh_from_db()
    assert subscription.amount_cents == 3990
