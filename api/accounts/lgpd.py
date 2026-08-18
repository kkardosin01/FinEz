"""
Exclusão LGPD completa — seção 5 da especificação.

1. Revoga consentimentos no agregador
2. Hard delete de transactions, accounts, connections, rules, budgets, whatsapp_*
3. `users` vira tombstone (email -> hash, nome -> null, deleted_at)

Um job semanal (accounts.tasks.check_orphan_records) confere órfãos.
"""
import hashlib
import logging

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger("finez")


def delete_user_data(user):
    # Imports locais: evita import circular entre apps no boot do Django.
    from budgets.models import Budget
    from connections.models import Connection
    from connections.pluggy_client import PluggyClient
    from transactions.models import Account, CategorizationRule, Transaction
    from whatsapp.models import WhatsappLink, WhatsappMessage

    # 1. Revoga consentimentos no agregador (best-effort — não bloqueia a exclusão local)
    client = PluggyClient()
    for connection in Connection.objects.filter(user=user):
        try:
            client.delete_item(connection.provider_item_id)
        except Exception:
            logger.exception(
                "pluggy_revoke_failed", extra={"connection_id": str(connection.id)}
            )

    with transaction.atomic():
        # 2. Hard delete
        Transaction.objects.filter(user=user).delete()
        CategorizationRule.objects.filter(user=user).delete()
        Account.objects.filter(user=user).delete()
        Connection.objects.filter(user=user).delete()
        Budget.objects.filter(user=user).delete()
        WhatsappMessage.objects.filter(user=user).delete()
        WhatsappLink.objects.filter(user=user).delete()

        # 3. Tombstone: mantém a linha (integridade referencial de invites) sem dado pessoal
        anonymized_email = hashlib.sha256(f"{user.id}{user.email}".encode()).hexdigest()
        user.email = f"deleted-{anonymized_email[:32]}@finez.invalid"
        user.name = None
        user.birth_date = None
        user.is_active = False
        user.deleted_at = timezone.now()
        user.set_unusable_password()
        user.save()
