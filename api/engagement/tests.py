from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from engagement.models import Badge, Streak
from engagement.services import award_badge, notify_badge_earned, record_activity
from engagement.tasks import check_spending_anomaly
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


def _tx(user, account, category, amount_cents, day, description="compra"):
    return Transaction.objects.create(
        user=user, account=account, category=category, amount_cents=amount_cents,
        description=description, date=day,
        category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )


# --- record_activity (streak) ---------------------------------------------------


def test_record_activity_starts_streak_at_one(user):
    record_activity(user)
    streak = Streak.objects.get(user=user)
    assert streak.current_streak == 1
    assert streak.longest_streak == 1


def test_record_activity_same_day_is_a_noop(user):
    record_activity(user)
    record_activity(user)
    streak = Streak.objects.get(user=user)
    assert streak.current_streak == 1


def test_record_activity_consecutive_days_increments_streak(user):
    yesterday = date.today() - timedelta(days=1)
    record_activity(user, on_date=yesterday)
    record_activity(user, on_date=date.today())
    streak = Streak.objects.get(user=user)
    assert streak.current_streak == 2
    assert streak.longest_streak == 2


def test_record_activity_gap_resets_streak(user):
    record_activity(user, on_date=date.today() - timedelta(days=5))
    record_activity(user, on_date=date.today())
    streak = Streak.objects.get(user=user)
    assert streak.current_streak == 1
    assert streak.longest_streak == 1  # recorde anterior era só 1 dia também


def test_record_activity_awards_streak_7_badge(user):
    start = date.today() - timedelta(days=6)
    new_badges = []
    for i in range(7):
        new_badges = record_activity(user, on_date=start + timedelta(days=i))
    assert len(new_badges) == 1
    assert new_badges[0].slug == Badge.Slug.STREAK_7
    assert Badge.objects.filter(user=user, slug=Badge.Slug.STREAK_7).exists()


def test_record_activity_does_not_reaward_same_badge(user):
    start = date.today() - timedelta(days=6)
    for i in range(7):
        record_activity(user, on_date=start + timedelta(days=i))
    assert Badge.objects.filter(user=user, slug=Badge.Slug.STREAK_7).count() == 1

    # streak continua, ainda não bateu o próximo marco (30) — não deve duplicar nem recriar a de 7 dias
    new_badges = record_activity(user, on_date=start + timedelta(days=7))
    assert new_badges == []
    assert Badge.objects.filter(user=user, slug=Badge.Slug.STREAK_7).count() == 1


# --- award_badge / notify_badge_earned ------------------------------------------


def test_award_badge_is_idempotent(user):
    _, created_first = award_badge(user, Badge.Slug.GOAL_ACHIEVER)
    _, created_second = award_badge(user, Badge.Slug.GOAL_ACHIEVER)
    assert created_first is True
    assert created_second is False
    assert Badge.objects.filter(user=user, slug=Badge.Slug.GOAL_ACHIEVER).count() == 1


def test_notify_badge_earned_sends_whatsapp_message(user, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    badge, _ = award_badge(user, Badge.Slug.GOAL_ACHIEVER)
    notify_badge_earned(user, badge)
    assert len(sent) == 1
    assert "conquista desbloqueada" in sent[0]


def test_notify_badge_earned_without_link_is_a_noop(user, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    badge, _ = award_badge(user, Badge.Slug.GOAL_ACHIEVER)
    notify_badge_earned(user, badge)
    assert sent == []


# --- check_spending_anomaly task -------------------------------------------------


def test_check_spending_anomaly_triggers_above_threshold(user, account, category, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    # histórico: média diária de R$ 10 nos últimos 60 dias (1 gasto de R$ 600 espalhado)
    _tx(user, account, category, -60000, date.today() - timedelta(days=1))
    # hoje: R$ 100, bem acima de 3x a média (~R$ 30)
    _tx(user, account, category, -10000, date.today())

    check_spending_anomaly(str(user.id))

    assert len(sent) == 1
    assert "gastou" in sent[0]


def test_check_spending_anomaly_ignores_insignificant_history(user, account, category, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    _tx(user, account, category, -1000, date.today())
    check_spending_anomaly(str(user.id))
    assert sent == []


def test_check_spending_anomaly_only_fires_once_per_day(user, account, category, monkeypatch):
    sent = []
    monkeypatch.setattr("whatsapp.sender.send_whatsapp_message", lambda phone, body: sent.append(body))
    WhatsappLink.objects.create(
        user=user, phone_e164="5511999999999", status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now(),
    )
    _tx(user, account, category, -60000, date.today() - timedelta(days=1))
    _tx(user, account, category, -10000, date.today())
    check_spending_anomaly(str(user.id))
    # segunda transação no mesmo dia, já acima do limiar — não deve reenviar
    _tx(user, account, category, -5000, date.today())
    check_spending_anomaly(str(user.id))
    assert len(sent) == 1


def test_check_spending_anomaly_unknown_user_is_a_noop():
    check_spending_anomaly("00000000-0000-0000-0000-000000000000")


# --- API view ---------------------------------------------------------------------


def test_engagement_summary_requires_authentication():
    response = APIClient().get("/api/engagement/summary")
    assert response.status_code in (401, 403)


def test_engagement_summary_returns_streak_and_badges(client, user):
    record_activity(user)
    award_badge(user, Badge.Slug.GOAL_ACHIEVER)

    response = client.get("/api/engagement/summary")
    assert response.status_code == 200
    assert response.data["streak"]["current_streak"] == 1
    assert len(response.data["badges"]) == 1
    assert response.data["badges"][0]["slug"] == Badge.Slug.GOAL_ACHIEVER
