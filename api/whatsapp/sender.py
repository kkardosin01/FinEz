"""Envio de mensagens via o adaptador Node (Baileys) — seção 6."""
import logging

import httpx
from django.conf import settings

logger = logging.getLogger("finez")


def send_whatsapp_message(phone_e164: str, body: str) -> None:
    try:
        response = httpx.post(
            f"{settings.WHATSAPP_ADAPTER_URL}/send",
            json={"phone": phone_e164, "body": body},
            headers={"Authorization": f"Bearer {settings.WHATSAPP_ADAPTER_TOKEN}"},
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        # Nunca derruba o fluxo por causa de uma falha de envio — loga e segue.
        logger.exception("whatsapp_send_failed", extra={"phone_suffix": phone_e164[-4:]})
