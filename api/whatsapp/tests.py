import hashlib
import hmac
import json
from datetime import date, timedelta

import httpx
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from budgets.models import Budget
from common.models import WebhookEvent
from transactions.models import Account, Category, Transaction
from whatsapp.handlers import handle_incoming_message
from whatsapp.llm_fallback import parse_with_llm
from whatsapp.models import WhatsappLink, WhatsappMessage
from whatsapp.parser import Intent, parse_message
from whatsapp.tasks import process_whatsapp_webhook, send_weekly_summaries, try_complete_pairing

pytestmark = pytest.mark.django_db


def test_parse_expense_with_keyword_category():
    parsed = parse_message("gastei 25,90 no mercado")
    assert parsed.intent == Intent.EXPENSE
    assert parsed.amount_cents == -2590
    assert parsed.category_slug == Category.Slug.GROCERIES


def test_parse_expense_without_known_keyword():
    parsed = parse_message("gastei 10 na padoca")
    assert parsed.intent == Intent.EXPENSE
    assert parsed.amount_cents == -1000
    assert parsed.category_slug is None


def test_parse_income():
    parsed = parse_message("recebi 1500 do freela")
    assert parsed.intent == Intent.INCOME
    assert parsed.amount_cents == 150000
    assert parsed.category_slug == Category.Slug.INCOME


def test_parse_correction():
    parsed = parse_message("era transporte")
    assert parsed.intent == Intent.CORRECTION
    assert parsed.category_slug == Category.Slug.TRANSPORT


def test_parse_query_month_spent():
    parsed = parse_message("quanto gastei esse mês?")
    assert parsed.intent == Intent.QUERY_MONTH_SPENT


def test_parse_unknown_falls_back():
    parsed = parse_message("oi tudo bem?")
    assert parsed.intent == Intent.UNKNOWN


def test_llm_fallback_not_configured(settings):
    settings.LLM_PROVIDER = ""
    settings.LLM_API_KEY = ""
    parsed = parse_with_llm("comprei um lanche por 15 conto")
    assert parsed.intent == Intent.UNKNOWN


def test_llm_fallback_unsupported_provider(settings):
    settings.LLM_PROVIDER = "openai"
    settings.LLM_API_KEY = "fake-key"
    parsed = parse_with_llm("comprei um lanche por 15 conto")
    assert parsed.intent == Intent.UNKNOWN


def test_llm_fallback_successful_extraction(settings, monkeypatch):
    settings.LLM_PROVIDER = "anthropic"
    settings.LLM_API_KEY = "fake-key"

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "input": {
                            "intent": "expense",
                            "amount_cents": -1500,
                            "description": "lanche",
                            "category_slug": "food",
                        },
                    }
                ]
            }

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse())

    parsed = parse_with_llm("comprei um lanche por 15 conto")
    assert parsed.intent == Intent.EXPENSE
    assert parsed.amount_cents == -1500
    assert parsed.description == "lanche"
    assert parsed.category_slug == Category.Slug.FOOD


def test_llm_fallback_no_tool_use_returns_unknown(settings, monkeypatch):
    settings.LLM_PROVIDER = "anthropic"
    settings.LLM_API_KEY = "fake-key"

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"type": "text", "text": "não entendi"}]}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse())

    parsed = parse_with_llm("oi tudo bem?")
    assert parsed.intent == Intent.UNKNOWN


def test_llm_fallback_http_error_returns_unknown(settings, monkeypatch):
    settings.LLM_PROVIDER = "anthropic"
    settings.LLM_API_KEY = "fake-key"

    def raise_error(*args, **kwargs):
        raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr(httpx, "post", raise_error)

    parsed = parse_with_llm("comprei um lanche por 15 conto")
    assert parsed.intent == Intent.UNKNOWN


def test_llm_fallback_invalid_category_slug_becomes_none(settings, monkeypatch):
    settings.LLM_PROVIDER = "anthropic"
    settings.LLM_API_KEY = "fake-key"

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "input": {
                            "intent": "query_month_spent",
                            "amount_cents": None,
                            "description": "quanto gastei esse mês",
                            "category_slug": "categoria-invalida",
                        },
                    }
                ]
            }

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: FakeResponse())

    parsed = parse_with_llm("quanto gastei esse mês?")
    assert parsed.intent == Intent.QUERY_MONTH_SPENT
    assert parsed.category_slug is None


# --- Webhook signature validation ------------------------------------------


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.mark.django_db
def test_whatsapp_webhook_with_valid_signature_is_enqueued(settings, monkeypatch):
    settings.WHATSAPP_WEBHOOK_SECRET = "webhook-secret"
    called = {}
    monkeypatch.setattr(
        "whatsapp.webhook_views.process_whatsapp_webhook.delay",
        lambda event_id: called.setdefault("event_id", event_id),
    )

    body = json.dumps({"phone": "5511999999999", "text": "gastei 20 no mercado"}).encode()
    signature = _sign("webhook-secret", body)

    response = APIClient().post(
        "/webhooks/whatsapp",
        data=body,
        content_type="application/json",
        HTTP_X_FINEZ_SIGNATURE=signature,
    )
    assert response.status_code == 200
    event = WebhookEvent.objects.get()
    assert event.signature_valid is True
    assert called["event_id"] == str(event.id)


@pytest.mark.django_db
def test_whatsapp_webhook_with_invalid_signature_is_not_enqueued(settings, monkeypatch):
    settings.WHATSAPP_WEBHOOK_SECRET = "webhook-secret"
    monkeypatch.setattr(
        "whatsapp.webhook_views.process_whatsapp_webhook.delay",
        lambda event_id: pytest.fail("não deveria enfileirar com assinatura inválida"),
    )

    body = json.dumps({"phone": "5511999999999", "text": "gastei 20 no mercado"}).encode()
    response = APIClient().post(
        "/webhooks/whatsapp",
        data=body,
        content_type="application/json",
        HTTP_X_FINEZ_SIGNATURE="assinatura-forjada",
    )
    assert response.status_code == 200
    assert WebhookEvent.objects.get().signature_valid is False


# --- handle_incoming_message (end-to-end) -----------------------------------


@pytest.fixture
def user(db):
    return User.objects.create_user(email="teste@finez.app", password="senha-forte-123")


@pytest.fixture
def other_categories(db):
    return {
        slug: Category.objects.create(slug=slug, name_pt=slug, color_light="#000000", color_dark="#ffffff")
        for slug in [Category.Slug.GROCERIES, Category.Slug.LEISURE, Category.Slug.OTHER, Category.Slug.INCOME]
    }


@pytest.mark.django_db
def test_handle_expense_message_creates_transaction(user, other_categories, monkeypatch):
    monkeypatch.setattr("whatsapp.handlers.check_budget_alerts.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.detect_subscriptions.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.check_spending_anomaly.delay", lambda user_id: None)

    reply = handle_incoming_message(user, "gastei 25,90 no mercado")

    transaction = Transaction.objects.get(user=user)
    assert transaction.amount_cents == -2590
    assert transaction.category.slug == Category.Slug.GROCERIES
    assert transaction.origin == Transaction.Origin.WHATSAPP
    assert "25.90" in reply or "25,90" in reply


@pytest.mark.django_db
def test_handle_expense_without_known_category_falls_back_to_other(user, other_categories, monkeypatch):
    monkeypatch.setattr("whatsapp.handlers.check_budget_alerts.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.detect_subscriptions.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.check_spending_anomaly.delay", lambda user_id: None)

    handle_incoming_message(user, "gastei 10 na padoca")

    transaction = Transaction.objects.get(user=user)
    assert transaction.category.slug == Category.Slug.OTHER


@pytest.mark.django_db
def test_handle_correction_recategorizes_last_transaction(user, other_categories, monkeypatch):
    monkeypatch.setattr("whatsapp.handlers.check_budget_alerts.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.detect_subscriptions.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.check_spending_anomaly.delay", lambda user_id: None)
    handle_incoming_message(user, "gastei 10 na balada")

    reply = handle_incoming_message(user, "era lazer")

    transaction = Transaction.objects.get(user=user)
    assert transaction.category.slug == Category.Slug.LEISURE
    assert "recategorizado" in reply


@pytest.mark.django_db
def test_handle_correction_without_prior_transaction_replies_gracefully(user, other_categories):
    reply = handle_incoming_message(user, "era lazer")
    assert "não achei" in reply


@pytest.mark.django_db
def test_handle_query_month_spent(user, other_categories, monkeypatch):
    monkeypatch.setattr("whatsapp.handlers.check_budget_alerts.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.detect_subscriptions.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.check_spending_anomaly.delay", lambda user_id: None)
    handle_incoming_message(user, "gastei 30 no mercado")

    reply = handle_incoming_message(user, "quanto gastei esse mês?")
    assert "30.00" in reply


@pytest.mark.django_db
def test_handle_query_budget_remaining_without_budget_set(user, other_categories):
    reply = handle_incoming_message(user, "quanto sobrou do orçamento de lazer")
    assert "não tem orçamento" in reply


@pytest.mark.django_db
def test_handle_query_budget_remaining_with_budget_set(user, other_categories, monkeypatch):
    monkeypatch.setattr("whatsapp.handlers.check_budget_alerts.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.detect_subscriptions.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.check_spending_anomaly.delay", lambda user_id: None)
    Budget.objects.create(
        user=user, category=other_categories[Category.Slug.LEISURE], amount_cents=10000, month=date.today().replace(day=1)
    )
    handle_incoming_message(user, "gastei 30 no lazer")

    reply = handle_incoming_message(user, "quanto sobrou do orçamento de lazer")
    assert "sobrou" in reply


@pytest.mark.django_db
def test_handle_unrecognized_message_returns_help(user):
    reply = handle_incoming_message(user, "oi tudo bem?")
    assert reply == "não entendi 🤔 tenta assim: *gastei 30 no mercado*"


# --- process_whatsapp_webhook task ------------------------------------------


def test_process_webhook_from_unlinked_phone_sends_pairing_instructions(monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "whatsapp.sender.send_whatsapp_message",
        lambda phone, body: sent.update(phone=phone, body=body),
    )
    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.WHATSAPP,
        payload={"phone": "5511999999999", "text": "oi"},
        signature_valid=True,
    )

    process_whatsapp_webhook(str(event.id))

    assert sent["phone"] == "5511999999999"
    assert "vincular" in sent["body"].lower()
    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.PROCESSED


def test_process_webhook_from_unlinked_phone_with_pairing_code_delegates(monkeypatch):
    triggered = {}
    monkeypatch.setattr(
        "whatsapp.tasks.try_complete_pairing.delay",
        lambda phone, code: triggered.update(phone=phone, code=code),
    )
    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.WHATSAPP,
        payload={"phone": "5511999999999", "text": "123456"},
        signature_valid=True,
    )

    process_whatsapp_webhook(str(event.id))

    assert triggered == {"phone": "5511999999999", "code": "123456"}


def test_process_webhook_from_linked_phone_handles_message_and_replies(user, monkeypatch):
    link = WhatsappLink.objects.create(
        user=user,
        phone_e164="5511999999999",
        status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now() + timedelta(minutes=10),
    )
    Category.objects.create(
        slug=Category.Slug.GROCERIES, name_pt="Mercado", color_light="#000000", color_dark="#ffffff"
    )
    sent = {}
    monkeypatch.setattr(
        "whatsapp.sender.send_whatsapp_message",
        lambda phone, body: sent.update(phone=phone, body=body),
    )
    monkeypatch.setattr("whatsapp.handlers.check_budget_alerts.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.detect_subscriptions.delay", lambda user_id: None)
    monkeypatch.setattr("whatsapp.handlers.check_spending_anomaly.delay", lambda user_id: None)

    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.WHATSAPP,
        payload={"phone": "5511999999999", "text": "gastei 20 no mercado"},
        signature_valid=True,
    )

    process_whatsapp_webhook(str(event.id))

    assert Transaction.objects.filter(user=user).exists()
    assert sent["phone"] == "5511999999999"
    messages = list(WhatsappMessage.objects.filter(user=user).order_by("created_at"))
    assert [m.direction for m in messages] == [WhatsappMessage.Direction.IN, WhatsappMessage.Direction.OUT]
    link.refresh_from_db()
    assert link.last_message_at is not None
    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.PROCESSED


def test_process_webhook_failure_marks_event_failed(user, monkeypatch):
    WhatsappLink.objects.create(
        user=user,
        phone_e164="5511999999999",
        status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now() + timedelta(minutes=10),
    )
    monkeypatch.setattr(
        "whatsapp.handlers.handle_incoming_message",
        lambda user, text: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.WHATSAPP,
        payload={"phone": "5511999999999", "text": "oi"},
        signature_valid=True,
    )

    with pytest.raises(Exception):
        process_whatsapp_webhook(str(event.id))

    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.FAILED
    assert event.attempts == 1


# --- try_complete_pairing task -----------------------------------------------


def test_try_complete_pairing_with_valid_code_activates_link(user, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "whatsapp.sender.send_whatsapp_message",
        lambda phone, body: sent.update(phone=phone, body=body),
    )
    link = WhatsappLink.objects.create(
        user=user,
        pairing_code="123456",
        status=WhatsappLink.Status.PENDING,
        pairing_expires_at=timezone.now() + timedelta(minutes=10),
    )

    try_complete_pairing("5511999999999", "123456")

    link.refresh_from_db()
    assert link.status == WhatsappLink.Status.ACTIVE
    assert link.phone_e164 == "5511999999999"
    assert "vinculado" in sent["body"]


def test_try_complete_pairing_with_expired_code_sends_error(user, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "whatsapp.sender.send_whatsapp_message",
        lambda phone, body: sent.update(phone=phone, body=body),
    )
    WhatsappLink.objects.create(
        user=user,
        pairing_code="123456",
        status=WhatsappLink.Status.PENDING,
        pairing_expires_at=timezone.now() - timedelta(minutes=1),
    )

    try_complete_pairing("5511999999999", "123456")

    assert "inválido" in sent["body"] or "expirado" in sent["body"]


def test_try_complete_pairing_with_unknown_code_sends_error(monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "whatsapp.sender.send_whatsapp_message",
        lambda phone, body: sent.update(phone=phone, body=body),
    )

    try_complete_pairing("5511999999999", "000000")

    assert "inválido" in sent["body"] or "expirado" in sent["body"]


# --- send_weekly_summaries task ----------------------------------------------


def test_send_weekly_summaries_reports_income_expense_and_balance(user, monkeypatch):
    WhatsappLink.objects.create(
        user=user,
        phone_e164="5511999999999",
        status=WhatsappLink.Status.ACTIVE,
        pairing_expires_at=timezone.now() + timedelta(minutes=10),
    )
    category = Category.objects.create(
        slug=Category.Slug.OTHER, name_pt="Outros", color_light="#000000", color_dark="#ffffff"
    )
    account = Account.objects.create(user=user, type=Account.Type.MANUAL, name="Manual")
    today = date.today()
    Transaction.objects.create(
        user=user, account=account, category=category, amount_cents=-3000, description="gasto",
        date=today, category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )
    Transaction.objects.create(
        user=user, account=account, category=category, amount_cents=10000, description="entrada",
        date=today, category_source=Transaction.CategorySource.USER, origin=Transaction.Origin.WEB,
    )

    sent = {}
    monkeypatch.setattr(
        "whatsapp.sender.send_whatsapp_message",
        lambda phone, body: sent.update(phone=phone, body=body),
    )

    send_weekly_summaries()

    assert sent["phone"] == "5511999999999"
    assert "entradas: R$ 100.00" in sent["body"]
    assert "saídas: R$ 30.00" in sent["body"]
    assert "balanço: R$ 70.00" in sent["body"]


def test_send_weekly_summaries_skips_unlinked_users(monkeypatch):
    sent_calls = []
    monkeypatch.setattr(
        "whatsapp.sender.send_whatsapp_message",
        lambda phone, body: sent_calls.append((phone, body)),
    )

    send_weekly_summaries()

    assert sent_calls == []
