import hashlib
import hmac
import json

import pytest
from cryptography.fernet import Fernet
from rest_framework.test import APIClient

from accounts.models import User
from common.models import WebhookEvent
from connections.models import Connection
from connections.pluggy_client import PluggyClient
from connections.tasks import process_pluggy_webhook, sync_connection_by_item_id
from transactions.models import Account, Category, Transaction

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="teste@finez.app", password="senha-forte-123")


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


# --- Connection.access_token encryption -----------------------------------


def test_connection_access_token_is_never_stored_in_plaintext(settings, user):
    settings.FERNET_KEY = Fernet.generate_key().decode()
    connection = Connection.objects.create(
        user=user, provider_item_id="item-1", institution_name="Banco Teste"
    )
    connection.set_access_token("token-real-do-pluggy")
    assert "token-real-do-pluggy" not in connection.access_token_encrypted
    assert connection.get_access_token() == "token-real-do-pluggy"


# --- Webhook signature validation ------------------------------------------


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_with_valid_signature_is_accepted_and_enqueued(settings, monkeypatch):
    settings.PLUGGY_WEBHOOK_SECRET = "webhook-secret"
    called = {}
    monkeypatch.setattr(
        "connections.webhook_views.process_pluggy_webhook.delay",
        lambda event_id: called.setdefault("event_id", event_id),
    )

    body = json.dumps({"event": "item/updated", "itemId": "item-1"}).encode()
    signature = _sign("webhook-secret", body)

    response = APIClient().post(
        "/webhooks/aggregator",
        data=body,
        content_type="application/json",
        HTTP_X_PLUGGY_SIGNATURE=signature,
    )
    assert response.status_code == 200
    event = WebhookEvent.objects.get()
    assert event.signature_valid is True
    assert called["event_id"] == str(event.id)


def test_webhook_with_invalid_signature_is_recorded_but_not_enqueued(settings, monkeypatch):
    settings.PLUGGY_WEBHOOK_SECRET = "webhook-secret"
    monkeypatch.setattr(
        "connections.webhook_views.process_pluggy_webhook.delay",
        lambda event_id: pytest.fail("não deveria enfileirar com assinatura inválida"),
    )

    body = json.dumps({"event": "item/updated"}).encode()
    response = APIClient().post(
        "/webhooks/aggregator",
        data=body,
        content_type="application/json",
        HTTP_X_PLUGGY_SIGNATURE="assinatura-forjada",
    )
    assert response.status_code == 200  # sempre 200, pra evitar retry infinito do provedor
    event = WebhookEvent.objects.get()
    assert event.signature_valid is False


def test_webhook_without_signature_header_is_rejected(settings):
    settings.PLUGGY_WEBHOOK_SECRET = "webhook-secret"
    body = json.dumps({"event": "item/updated"}).encode()
    response = APIClient().post("/webhooks/aggregator", data=body, content_type="application/json")
    assert response.status_code == 200
    assert WebhookEvent.objects.get().signature_valid is False


def test_webhook_without_secret_configured_only_accepts_in_debug(settings):
    settings.PLUGGY_WEBHOOK_SECRET = ""

    settings.DEBUG = True
    body = json.dumps({"event": "item/updated"}).encode()
    response = APIClient().post("/webhooks/aggregator", data=body, content_type="application/json")
    assert WebhookEvent.objects.get().signature_valid is True

    WebhookEvent.objects.all().delete()
    settings.DEBUG = False
    response = APIClient().post("/webhooks/aggregator", data=body, content_type="application/json")
    assert response.status_code == 200
    assert WebhookEvent.objects.get().signature_valid is False


def test_webhook_with_unparseable_body_still_returns_200(settings):
    settings.PLUGGY_WEBHOOK_SECRET = "webhook-secret"
    body = b"isso nao e json"
    signature = _sign("webhook-secret", body)
    response = APIClient().post(
        "/webhooks/aggregator",
        data=body,
        content_type="application/json",
        HTTP_X_PLUGGY_SIGNATURE=signature,
    )
    assert response.status_code == 200
    assert WebhookEvent.objects.get().payload == {"_raw_unparseable": True}


# --- Connection views --------------------------------------------------------


def test_list_connections_only_returns_own(client, user):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    Connection.objects.create(user=user, provider_item_id="item-mine", institution_name="Meu banco")
    Connection.objects.create(user=other_user, provider_item_id="item-other", institution_name="Outro banco")

    response = client.get("/api/connections")
    assert response.status_code == 200
    assert [c["institution_name"] for c in response.data] == ["Meu banco"]


def test_callback_creates_connection_and_triggers_sync(client, user, monkeypatch):
    monkeypatch.setattr(
        PluggyClient, "get_item", lambda self, item_id: {"connector": {"name": "Nubank", "imageUrl": "x"}}
    )
    triggered = {}
    monkeypatch.setattr(
        "connections.views.sync_connection_by_item_id.delay",
        lambda item_id: triggered.setdefault("item_id", item_id),
    )

    response = client.post("/api/connections/callback", {"item_id": "item-123"})
    assert response.status_code == 201
    assert response.data["institution_name"] == "Nubank"
    assert triggered["item_id"] == "item-123"
    connection = Connection.objects.get(user=user)
    assert connection.status == Connection.Status.SYNCING


def test_callback_without_item_id_is_rejected(client):
    response = client.post("/api/connections/callback", {})
    assert response.status_code == 400


def test_delete_connection_revokes_locally_even_if_provider_call_fails(client, user, monkeypatch):
    """Regressão: exclusão local não pode ficar refém do agregador estar fora do ar (LGPD)."""
    connection = Connection.objects.create(
        user=user, provider_item_id="item-1", institution_name="Banco Teste", status=Connection.Status.ACTIVE
    )

    def _boom(self, item_id):
        raise RuntimeError("agregador fora do ar")

    monkeypatch.setattr(PluggyClient, "delete_item", _boom)

    response = client.delete(f"/api/connections/{connection.id}")
    assert response.status_code == 204
    connection.refresh_from_db()
    assert connection.status == Connection.Status.REVOKED


def test_cannot_delete_another_users_connection(client):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    connection = Connection.objects.create(
        user=other_user, provider_item_id="item-1", institution_name="Banco Teste"
    )
    response = client.delete(f"/api/connections/{connection.id}")
    assert response.status_code == 404


# --- process_pluggy_webhook task --------------------------------------------


def test_process_pluggy_webhook_item_created_triggers_sync(monkeypatch):
    triggered = {}
    monkeypatch.setattr(
        "connections.tasks.sync_connection_by_item_id.delay",
        lambda item_id: triggered.setdefault("item_id", item_id),
    )
    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.PLUGGY,
        payload={"event": "item/created", "itemId": "item-1"},
        signature_valid=True,
    )

    process_pluggy_webhook(str(event.id))

    assert triggered["item_id"] == "item-1"
    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.PROCESSED
    assert event.processed_at is not None


def test_process_pluggy_webhook_item_error_marks_connection_error(user):
    connection = Connection.objects.create(
        user=user, provider_item_id="item-1", institution_name="Banco Teste", status=Connection.Status.ACTIVE
    )
    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.PLUGGY,
        payload={"event": "item/error", "itemId": "item-1"},
        signature_valid=True,
    )

    process_pluggy_webhook(str(event.id))

    connection.refresh_from_db()
    assert connection.status == Connection.Status.ERROR
    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.PROCESSED


def test_process_pluggy_webhook_failure_marks_event_failed_and_retries(monkeypatch):
    monkeypatch.setattr(
        "connections.tasks.sync_connection_by_item_id.delay",
        lambda item_id: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.PLUGGY,
        payload={"event": "item/created", "itemId": "item-1"},
        signature_valid=True,
    )

    with pytest.raises(Exception):
        process_pluggy_webhook(str(event.id))

    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.FAILED
    assert event.attempts == 1
    assert "boom" in event.error_message


# --- sync_connection_by_item_id task ----------------------------------------


def test_sync_unknown_item_id_is_a_noop():
    sync_connection_by_item_id("item-nao-existe")  # não deve levantar exceção


def test_sync_connection_creates_accounts_and_transactions(settings, user, monkeypatch):
    settings.FERNET_KEY = Fernet.generate_key().decode()
    Category.objects.create(
        slug=Category.Slug.GROCERIES, name_pt="Mercado", color_light="#000000", color_dark="#ffffff"
    )
    Category.objects.create(slug=Category.Slug.OTHER, name_pt="Outros", color_light="#000000", color_dark="#ffffff")
    connection = Connection.objects.create(user=user, provider_item_id="item-1", institution_name="Banco Teste")

    monkeypatch.setattr(
        PluggyClient, "list_accounts", lambda self, item_id: [{"id": "acc-1", "type": "CHECKING", "name": "Conta"}]
    )
    monkeypatch.setattr(
        PluggyClient,
        "list_transactions",
        lambda self, account_id, page=1, page_size=500: {
            "results": [
                {
                    "id": "ptx-1",
                    "amount": -50.0,
                    "description": "Supermercado Extra",
                    "category": "Groceries",
                    "date": "2026-08-10T00:00:00.000Z",
                }
            ],
            "totalPages": 1,
        },
    )
    monkeypatch.setattr("budgets.tasks.check_budget_alerts.delay", lambda user_id: None)

    sync_connection_by_item_id("item-1")

    connection.refresh_from_db()
    assert connection.status == Connection.Status.ACTIVE
    assert connection.last_synced_at is not None

    account = Account.objects.get(connection=connection)
    assert account.provider_account_id == "acc-1"

    transaction = Transaction.objects.get(account=account)
    assert transaction.amount_cents == -5000
    assert transaction.category.slug == Category.Slug.GROCERIES
    assert transaction.origin == Transaction.Origin.BANK

    # re-sync não deve duplicar (idempotência por provider_transaction_id)
    sync_connection_by_item_id("item-1")
    assert Transaction.objects.filter(account=account).count() == 1


def test_sync_connection_marks_error_and_retries_on_failure(settings, user, monkeypatch):
    settings.FERNET_KEY = Fernet.generate_key().decode()
    connection = Connection.objects.create(
        user=user, provider_item_id="item-1", institution_name="Banco Teste", status=Connection.Status.SYNCING
    )

    def _boom(self, item_id):
        raise RuntimeError("agregador fora do ar")

    monkeypatch.setattr(PluggyClient, "list_accounts", _boom)

    with pytest.raises(Exception):
        sync_connection_by_item_id("item-1")

    connection.refresh_from_db()
    assert connection.status == Connection.Status.ERROR
