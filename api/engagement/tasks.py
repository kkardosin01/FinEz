import logging
from datetime import date, timedelta

from celery import shared_task
from django.db.models import Sum

logger = logging.getLogger("finez")

ANOMALY_LOOKBACK_DAYS = 60
ANOMALY_MULTIPLIER = 3
ANOMALY_MIN_AVG_CENTS = 500  # evita alertar com histórico insignificante


@shared_task
def check_spending_anomaly(user_id: str):
    """
    Disparado na criação de toda transação (mesmo gancho do check_budget_alerts).
    Compara o total gasto hoje com a média diária dos últimos 60 dias e avisa se
    estourar bem acima do normal — só dispara no exato momento em que cruza o
    limiar (mesmo padrão de idempotência do alerta de orçamento).
    """
    from accounts.models import User
    from transactions.models import Transaction

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    today = date.today()
    window_start = today - timedelta(days=ANOMALY_LOOKBACK_DAYS)

    last_tx = (
        Transaction.objects.filter(user=user, date=today, amount_cents__lt=0).order_by("-created_at").first()
    )
    if not last_tx:
        return

    today_total = abs(
        Transaction.objects.filter(user=user, date=today, amount_cents__lt=0).aggregate(total=Sum("amount_cents"))[
            "total"
        ]
        or 0
    )
    total_before = today_total - abs(last_tx.amount_cents)

    history_total = abs(
        Transaction.objects.filter(
            user=user, date__gte=window_start, date__lt=today, amount_cents__lt=0
        ).aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    avg_daily = history_total / ANOMALY_LOOKBACK_DAYS
    if avg_daily < ANOMALY_MIN_AVG_CENTS:
        return

    threshold = avg_daily * ANOMALY_MULTIPLIER
    if total_before <= threshold < today_total:
        _notify_anomaly(user, today_total, avg_daily)


def _notify_anomaly(user, today_total_cents: int, avg_daily_cents: float) -> None:
    from whatsapp.models import WhatsappLink
    from whatsapp.sender import send_whatsapp_message

    link = WhatsappLink.objects.filter(user=user, status=WhatsappLink.Status.ACTIVE).first()
    message = (
        f"🚨 hoje você já gastou R$ {today_total_cents / 100:.2f}, bem acima da sua média "
        f"diária (R$ {avg_daily_cents / 100:.2f}). vale dar uma olhada 👀"
    )
    if link:
        send_whatsapp_message(link.phone_e164, message)
    logger.info("spending_anomaly_alert_triggered", extra={"user_id": str(user.id), "today_cents": today_total_cents})
