import logging

from celery import shared_task
from django.utils import timezone

from common.models import WebhookEvent
from transactions.categorization import categorize_provider_transaction
from transactions.models import Account, Transaction

from .models import Connection
from .pluggy_client import PluggyClient

logger = logging.getLogger("finez")


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def process_pluggy_webhook(self, event_id: str):
    event = WebhookEvent.objects.get(id=event_id)
    try:
        event_type = event.payload.get("event")
        item_id = event.payload.get("itemId") or event.payload.get("item", {}).get("id")

        if event_type in ("item/created", "item/updated"):
            sync_connection_by_item_id.delay(item_id)
        elif event_type == "item/error":
            Connection.objects.filter(provider_item_id=item_id).update(
                status=Connection.Status.ERROR
            )
        elif event_type == "transactions/created" or event_type == "transactions/updated":
            sync_connection_by_item_id.delay(item_id)

        event.status = WebhookEvent.Status.PROCESSED
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "processed_at"])
    except Exception as exc:
        event.attempts += 1
        event.error_message = str(exc)[:2000]
        event.status = WebhookEvent.Status.FAILED
        event.save(update_fields=["attempts", "error_message", "status"])
        logger.exception("pluggy_webhook_processing_failed", extra={"event_id": event_id})
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_connection_by_item_id(self, item_id: str):
    try:
        connection = Connection.objects.get(provider_item_id=item_id)
    except Connection.DoesNotExist:
        logger.warning("sync_unknown_item", extra={"item_id": item_id})
        return

    client = PluggyClient()
    try:
        provider_accounts = client.list_accounts(item_id)
        for provider_account in provider_accounts:
            account, _ = Account.objects.get_or_create(
                user=connection.user,
                connection=connection,
                provider_account_id=provider_account["id"],
                defaults={
                    "type": _map_account_type(provider_account.get("type")),
                    "name": provider_account.get("name", connection.institution_name),
                },
            )
            _sync_account_transactions(connection, account)

        connection.status = Connection.Status.ACTIVE
        connection.last_synced_at = timezone.now()
        connection.save(update_fields=["status", "last_synced_at", "updated_at"])
    except Exception as exc:
        connection.status = Connection.Status.ERROR
        connection.save(update_fields=["status", "updated_at"])
        logger.exception("connection_sync_failed", extra={"connection_id": str(connection.id)})
        raise self.retry(exc=exc)


def _map_account_type(provider_type: str | None) -> str:
    return Account.Type.CREDIT_CARD if provider_type == "CREDIT" else Account.Type.CHECKING


def _sync_account_transactions(connection: Connection, account: Account):
    from budgets.tasks import check_budget_alerts  # import local: evita ciclo entre apps
    from subscriptions.tasks import detect_subscriptions

    client = PluggyClient()
    page = 1
    while True:
        result = client.list_transactions(account.provider_account_id, page=page)
        items = result.get("results", [])
        if not items:
            break

        for item in items:
            category, source = categorize_provider_transaction(
                connection.user, item.get("description", ""), item.get("category")
            )
            # Idempotência: provider_transaction_id UNIQUE por account (regra de ouro §5)
            _, created = Transaction.objects.update_or_create(
                account=account,
                provider_transaction_id=item["id"],
                defaults={
                    "user": connection.user,
                    "amount_cents": round(item["amount"] * 100),
                    "description": item.get("description", ""),
                    "date": item["date"][:10],
                    "category": category,
                    "category_source": source,
                    "origin": Transaction.Origin.BANK,
                    "raw_provider_data": item,
                },
            )
            if created:
                check_budget_alerts.delay(str(connection.user_id))
                detect_subscriptions.delay(str(connection.user_id))

        if page >= result.get("totalPages", 1):
            break
        page += 1
