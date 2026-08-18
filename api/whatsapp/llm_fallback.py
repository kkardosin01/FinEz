"""
Fallback do parser via LLM (seção 6) — só acionado quando a heurística falha.

Provedor escolhido na implementação, pelo preço do momento (pendência aberta,
não bloqueia o MVP). Interpretação do LLM vira `categorization_rule`, então
o custo tende a zero com o uso — ver `whatsapp.handlers`.
"""
import logging

from django.conf import settings

from .parser import Intent, ParsedMessage

logger = logging.getLogger("finez")


def parse_with_llm(text: str) -> ParsedMessage:
    if not settings.LLM_PROVIDER or not settings.LLM_API_KEY:
        logger.info("llm_fallback_not_configured")
        return ParsedMessage(intent=Intent.UNKNOWN, description=text)

    # TODO: implementar chamada ao provedor escolhido (seção 6, pendência aberta).
    # Contrato esperado: extrair {intent, amount_cents, description, category_slug}
    # do texto livre e retornar ParsedMessage. Manter o prompt curto e determinístico
    # (poucos tokens) já que roda por mensagem.
    logger.warning("llm_fallback_not_implemented", extra={"provider": settings.LLM_PROVIDER})
    return ParsedMessage(intent=Intent.UNKNOWN, description=text)
