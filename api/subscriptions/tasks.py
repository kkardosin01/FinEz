import logging
from datetime import date, timedelta

from celery import shared_task

from .detection import find_recurring_candidates
from .models import Subscription

logger = logging.getLogger("finez")

REMINDER_LEAD_DAYS = 3
ASSUMED_CYCLE_DAYS = 30


@shared_task
def detect_subscriptions(user_id: str):
    """
    Disparado após sync bancário e após lançamento de gasto via WhatsApp (mesmo
    gatilho de `check_budget_alerts`). Atualiza/cria assinaturas detectadas e
    alerta o usuário via WhatsApp quando o valor de uma assinatura já conhecida sobe.
    """
    from accounts.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    for merchant_key, txs in find_recurring_candidates(user):
        latest = txs[-1]
        amount_cents = abs(latest.amount_cents)

        subscription, created = Subscription.objects.get_or_create(
            user=user,
            merchant_key=merchant_key,
            defaults={
                "name": latest.description.strip(),
                "category": latest.category,
                "amount_cents": amount_cents,
                "last_charged_at": latest.date,
            },
        )
        if created or subscription.status == Subscription.Status.CANCELED:
            continue

        subscription.last_charged_at = latest.date
        update_fields = ["last_charged_at", "updated_at"]
        if amount_cents != subscription.amount_cents:
            if amount_cents > subscription.amount_cents:
                _notify_price_increase(subscription, amount_cents)
            subscription.previous_amount_cents = subscription.amount_cents
            subscription.amount_cents = amount_cents
            update_fields += ["previous_amount_cents", "amount_cents"]
        subscription.save(update_fields=update_fields)


@shared_task
def remind_upcoming_charges():
    """
    Celery Beat, diário (notificação proativa — seção 3): lembra o usuário de
    assinaturas ativas com cobrança prevista em ~3 dias. Cadência assumida de
    30 dias (heurística — não temos a data exata da próxima cobrança).
    """
    today = date.today()
    target_date = today + timedelta(days=REMINDER_LEAD_DAYS)

    for subscription in Subscription.objects.filter(status=Subscription.Status.ACTIVE).select_related("user"):
        next_expected = subscription.last_charged_at + timedelta(days=ASSUMED_CYCLE_DAYS)
        if next_expected == target_date:
            _notify_upcoming_charge(subscription)


def _notify_upcoming_charge(subscription: Subscription) -> None:
    from whatsapp.models import WhatsappLink
    from whatsapp.sender import send_whatsapp_message

    link = WhatsappLink.objects.filter(user=subscription.user, status=WhatsappLink.Status.ACTIVE).first()
    amount_reais = subscription.amount_cents / 100
    if link:
        send_whatsapp_message(
            link.phone_e164,
            f"🔔 sua assinatura *{subscription.name}* deve cobrar R$ {amount_reais:.2f} em ~{REMINDER_LEAD_DAYS} dias.",
        )
    logger.info(
        "subscription_charge_reminder_sent",
        extra={"user_id": str(subscription.user_id), "subscription_id": str(subscription.id)},
    )


def _notify_price_increase(subscription: Subscription, new_amount_cents: int) -> None:
    from whatsapp.models import WhatsappLink
    from whatsapp.sender import send_whatsapp_message

    link = WhatsappLink.objects.filter(user=subscription.user, status=WhatsappLink.Status.ACTIVE).first()
    old_reais = subscription.amount_cents / 100
    new_reais = new_amount_cents / 100
    if link:
        send_whatsapp_message(
            link.phone_e164,
            f"📈 Sua assinatura *{subscription.name}* ficou mais cara: "
            f"de R$ {old_reais:.2f} pra R$ {new_reais:.2f} por mês.",
        )
    logger.info(
        "subscription_price_increase",
        extra={"user_id": str(subscription.user_id), "subscription_id": str(subscription.id)},
    )
