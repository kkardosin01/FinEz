import logging
from datetime import date, timedelta

from celery import shared_task
from django.db.models import Q, Sum
from django.utils import timezone

from common.models import WebhookEvent

logger = logging.getLogger("finez")

PAIRING_INSTRUCTIONS = (
    "esse número ainda não tá vinculado a nenhuma conta 👋\n"
    "gera um código em finez.app -> Conta -> Vincular WhatsApp e manda ele aqui"
)


@shared_task(bind=True, max_retries=5, default_retry_delay=15)
def process_whatsapp_webhook(self, event_id: str):
    """Webhook só enfileira; este worker processa (princípio da seção 4)."""
    from .handlers import handle_incoming_message
    from .models import WhatsappLink, WhatsappMessage
    from .sender import send_whatsapp_message

    event = WebhookEvent.objects.get(id=event_id)
    try:
        phone = event.payload["phone"]
        text = event.payload.get("text", "")

        link = _resolve_link(phone)
        if link is None:
            if text.strip().isdigit() and len(text.strip()) == 6:
                try_complete_pairing.delay(phone, text.strip())
            else:
                send_whatsapp_message(phone, PAIRING_INSTRUCTIONS)
            _mark_processed(event)
            return

        WhatsappMessage.objects.create(
            user=link.user, direction=WhatsappMessage.Direction.IN, body=text
        )
        reply = handle_incoming_message(link.user, text)
        WhatsappMessage.objects.create(
            user=link.user, direction=WhatsappMessage.Direction.OUT, body=reply
        )
        send_whatsapp_message(phone, reply)

        link.last_message_at = timezone.now()
        link.save(update_fields=["last_message_at"])

        _mark_processed(event)
    except Exception as exc:
        event.attempts += 1
        event.error_message = str(exc)[:2000]
        event.status = WebhookEvent.Status.FAILED
        event.save(update_fields=["attempts", "error_message", "status"])
        logger.exception("whatsapp_webhook_processing_failed", extra={"event_id": event_id})
        raise self.retry(exc=exc)


def _resolve_link(phone: str):
    from .models import WhatsappLink

    # Tenta casar com número pareado (ativo) ou pendente de pareamento por código
    return WhatsappLink.objects.filter(phone_e164=phone, status=WhatsappLink.Status.ACTIVE).first()


def _mark_processed(event: WebhookEvent) -> None:
    event.status = WebhookEvent.Status.PROCESSED
    event.processed_at = timezone.now()
    event.save(update_fields=["status", "processed_at"])


@shared_task(bind=True, max_retries=5, default_retry_delay=15)
def try_complete_pairing(self, phone: str, pairing_code: str):
    """
    Mensagem recebida de número não pareado contendo um código de 6 dígitos:
    tenta casar com um WhatsappLink pendente.
    """
    from .models import WhatsappLink
    from .sender import send_whatsapp_message

    link = WhatsappLink.objects.filter(
        pairing_code=pairing_code, status=WhatsappLink.Status.PENDING
    ).first()
    if not link or not link.is_pairing_code_valid():
        send_whatsapp_message(phone, "código inválido ou expirado. gera um novo em finez.app -> Conta")
        return

    link.phone_e164 = phone
    link.status = WhatsappLink.Status.ACTIVE
    link.save(update_fields=["phone_e164", "status"])
    send_whatsapp_message(
        phone,
        "prontinho, seu WhatsApp tá vinculado! ✓\nmanda algo tipo *gastei 25 no lanche* pra testar",
    )


@shared_task
def send_weekly_summaries():
    """Celery Beat — domingo à noite (seção 4)."""
    from transactions.models import Transaction

    from .models import WhatsappLink
    from .sender import send_whatsapp_message

    today = date.today()
    week_start = today - timedelta(days=7)

    for link in WhatsappLink.objects.filter(status=WhatsappLink.Status.ACTIVE).select_related("user"):
        totals = Transaction.objects.filter(
            user=link.user, date__gte=week_start, date__lte=today
        ).aggregate(
            income=Sum("amount_cents", filter=Q(amount_cents__gt=0)),
            expense=Sum("amount_cents", filter=Q(amount_cents__lt=0)),
        )
        income = (totals["income"] or 0) / 100
        expense = abs(totals["expense"] or 0) / 100
        message = (
            f"resumo da semana 📊\n"
            f"entradas: R$ {income:.2f}\n"
            f"saídas: R$ {expense:.2f}\n"
            f"balanço: R$ {income - expense:.2f}"
        )
        send_whatsapp_message(link.phone_e164, message)
