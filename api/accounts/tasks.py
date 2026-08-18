import logging

from celery import shared_task

logger = logging.getLogger("finez")


@shared_task
def check_orphan_records():
    """Job semanal: confere que a exclusão LGPD não deixou órfãos (seção 5)."""
    from budgets.models import Budget
    from connections.models import Connection
    from transactions.models import Account, CategorizationRule, Transaction
    from whatsapp.models import WhatsappLink, WhatsappMessage

    orphan_counts = {
        "transactions": Transaction.objects.filter(user__deleted_at__isnull=False).count(),
        "accounts": Account.objects.filter(user__deleted_at__isnull=False).count(),
        "connections": Connection.objects.filter(user__deleted_at__isnull=False).count(),
        "rules": CategorizationRule.objects.filter(user__deleted_at__isnull=False).count(),
        "budgets": Budget.objects.filter(user__deleted_at__isnull=False).count(),
        "whatsapp_links": WhatsappLink.objects.filter(user__deleted_at__isnull=False).count(),
        "whatsapp_messages": WhatsappMessage.objects.filter(user__deleted_at__isnull=False).count(),
    }
    total = sum(orphan_counts.values())
    if total:
        logger.error("lgpd_orphan_records_found", extra=orphan_counts)
    else:
        logger.info("lgpd_orphan_check_clean")
    return orphan_counts
