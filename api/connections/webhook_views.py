import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from common.models import WebhookEvent

from .tasks import process_pluggy_webhook

logger = logging.getLogger("finez")


def _signature_valid(raw_body: bytes, signature_header: str | None) -> bool:
    if not settings.PLUGGY_WEBHOOK_SECRET:
        return settings.DEBUG  # sandbox sem secret configurado: só aceita em DEBUG
    if not signature_header:
        return False
    expected = hmac.new(
        settings.PLUGGY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@csrf_exempt
@require_POST
@ratelimit(key="ip", rate="120/m", block=True)
def pluggy_webhook(request):
    """
    Webhooks só enfileiram, workers processam (princípio da seção 4).
    Valida a assinatura, grava o evento bruto e responde 200 em milissegundos.
    """
    raw_body = request.body
    signature_header = request.headers.get("X-Pluggy-Signature")
    valid = _signature_valid(raw_body, signature_header)

    try:
        payload = json.loads(raw_body or b"{}")
    except json.JSONDecodeError:
        payload = {"_raw_unparseable": True}

    event = WebhookEvent.objects.create(
        source=WebhookEvent.Source.PLUGGY, payload=payload, signature_valid=valid
    )

    if not valid:
        logger.warning("pluggy_webhook_invalid_signature", extra={"event_id": str(event.id)})
        return HttpResponse(status=200)  # responde 200 mesmo assim: evita retry infinito do provedor

    process_pluggy_webhook.delay(str(event.id))
    return HttpResponse(status=200)
