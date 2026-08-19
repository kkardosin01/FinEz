"""
Fallback do parser via LLM (seção 6) — só acionado quando a heurística falha.

Provedor: Anthropic (Claude Haiku), pelo custo/latência baixos — adequado pra
rodar por mensagem. Usa tool-use pra forçar saída estruturada, sem parsing de
texto livre. Interpretação do LLM vira `categorization_rule` no fluxo normal
de `whatsapp.handlers`, então o custo tende a cair com o uso.
"""
import logging

import httpx
from django.conf import settings

from transactions.models import Category

from .parser import Intent, ParsedMessage

logger = logging.getLogger("finez")

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"

_VALID_SLUGS = [choice.value for choice in Category.Slug]
_VALID_INTENTS = [intent.value for intent in Intent if intent != Intent.UNKNOWN]

_SYSTEM_PROMPT = (
    "Você interpreta mensagens de WhatsApp sobre finanças pessoais em português "
    "informal, de um público de 16 a 25 anos. A heurística por regex não reconheceu "
    "a mensagem recebida. Se ela for sobre lançar um gasto/recebimento, consultar "
    "gasto do mês/orçamento, ou corrigir a categoria do último lançamento, chame a "
    "ferramenta `parse_finance_message` com os dados extraídos. Se não for nada "
    "disso (ex: saudação, pergunta fora do escopo), não chame nenhuma ferramenta."
)

_TOOL_SCHEMA = {
    "name": "parse_finance_message",
    "description": "Extrai intenção e dados estruturados de uma mensagem de finanças pessoais.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": _VALID_INTENTS},
            "amount_cents": {
                "type": ["integer", "null"],
                "description": (
                    "Valor em centavos. Negativo pra gasto, positivo pra recebimento. "
                    "Null se a intenção não envolver valor (consulta/correção)."
                ),
            },
            "description": {
                "type": "string",
                "description": "Descrição curta do lançamento (ex: 'lanche', 'uber pro trampo').",
            },
            "category_slug": {
                "type": ["string", "null"],
                "enum": [*_VALID_SLUGS, None],
                "description": "Categoria mais provável. Null se não der pra inferir.",
            },
        },
        "required": ["intent"],
    },
}


def parse_with_llm(text: str) -> ParsedMessage:
    if not settings.LLM_PROVIDER or not settings.LLM_API_KEY:
        logger.info("llm_fallback_not_configured")
        return ParsedMessage(intent=Intent.UNKNOWN, description=text)

    if settings.LLM_PROVIDER != "anthropic":
        logger.warning("llm_fallback_unsupported_provider", extra={"provider": settings.LLM_PROVIDER})
        return ParsedMessage(intent=Intent.UNKNOWN, description=text)

    try:
        extracted = _call_anthropic(text)
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.warning("llm_fallback_call_failed", extra={"error": str(exc)})
        return ParsedMessage(intent=Intent.UNKNOWN, description=text)

    if extracted is None:
        return ParsedMessage(intent=Intent.UNKNOWN, description=text)

    try:
        intent = Intent(extracted["intent"])
    except (KeyError, ValueError):
        return ParsedMessage(intent=Intent.UNKNOWN, description=text)

    category_slug = extracted.get("category_slug")
    if category_slug not in _VALID_SLUGS:
        category_slug = None

    return ParsedMessage(
        intent=intent,
        amount_cents=extracted.get("amount_cents"),
        description=(extracted.get("description") or text).strip(),
        category_slug=category_slug,
    )


def _call_anthropic(text: str) -> dict | None:
    response = httpx.post(
        _ANTHROPIC_URL,
        headers={
            "x-api-key": settings.LLM_API_KEY,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        json={
            "model": settings.LLM_MODEL,
            "max_tokens": 256,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": text}],
            "tools": [_TOOL_SCHEMA],
        },
        timeout=8.0,
    )
    response.raise_for_status()
    data = response.json()
    for block in data.get("content", []):
        if block.get("type") == "tool_use":
            return block.get("input")
    return None
