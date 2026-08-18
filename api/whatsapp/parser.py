"""
Parser em duas camadas (seção 4): regex/heurística primeiro, LLM só quando
a heurística falha. Cobre lançamento, consulta e correção.
"""
import re
from dataclasses import dataclass
from enum import Enum

from transactions.models import Category

_AMOUNT = r"(?P<amount>\d+(?:[.,]\d{1,2})?)"

_EXPENSE_PATTERNS = [
    re.compile(rf"gastei\s+{_AMOUNT}\s+(?:no|na|com|em)\s+(?P<desc>.+)", re.IGNORECASE),
    re.compile(rf"paguei\s+{_AMOUNT}\s+(?:de|do|da|no|na|em)\s+(?P<desc>.+)", re.IGNORECASE),
]
_INCOME_PATTERNS = [
    re.compile(rf"receb[ie]\s*(?:i|do)?\s+{_AMOUNT}(?:\s+(?:de|do|da)\s+(?P<desc>.+))?", re.IGNORECASE),
]
_CORRECTION_PATTERN = re.compile(r"^(?:era|muda(?:r)?\s+(?:pra|para))\s+(?P<category>.+)$", re.IGNORECASE)
_QUERY_MONTH_PATTERN = re.compile(r"quanto\s+gastei.*(?:esse|neste|no)\s+m[eê]s", re.IGNORECASE)
_QUERY_BUDGET_PATTERN = re.compile(
    r"quanto\s+sobrou\s+(?:do|de)\s+or[çc]amento\s+(?:de|do|da)\s+(?P<category>\w+)", re.IGNORECASE
)

# Palavras-chave -> categoria: heurística de categorização a partir da descrição livre.
_KEYWORD_CATEGORY = {
    Category.Slug.FOOD: ["lanche", "restaurante", "ifood", "almoço", "almoco", "jantar", "café", "cafe"],
    Category.Slug.GROCERIES: ["mercado", "supermercado", "feira", "hortifruti"],
    Category.Slug.TRANSPORT: ["uber", "99", "ônibus", "onibus", "gasolina", "combustível", "combustivel", "metrô", "metro"],
    Category.Slug.SUBSCRIPTIONS: ["netflix", "spotify", "assinatura", "mensalidade"],
    Category.Slug.HEALTH: ["farmácia", "farmacia", "remédio", "remedio", "médico", "medico", "consulta"],
    Category.Slug.LEISURE: ["cinema", "bar", "show", "festa", "jogo", "lazer"],
    Category.Slug.HOUSING: ["aluguel", "condomínio", "condominio", "luz", "água", "agua", "internet"],
}

# Aliases usados na correção via chat ("era transporte") -> slug da categoria.
_CATEGORY_ALIASES = {
    "mercado": Category.Slug.GROCERIES,
    "alimentação": Category.Slug.FOOD,
    "alimentacao": Category.Slug.FOOD,
    "comida": Category.Slug.FOOD,
    "transporte": Category.Slug.TRANSPORT,
    "assinatura": Category.Slug.SUBSCRIPTIONS,
    "assinaturas": Category.Slug.SUBSCRIPTIONS,
    "saúde": Category.Slug.HEALTH,
    "saude": Category.Slug.HEALTH,
    "lazer": Category.Slug.LEISURE,
    "moradia": Category.Slug.HOUSING,
    "receita": Category.Slug.INCOME,
    "outros": Category.Slug.OTHER,
}


class Intent(Enum):
    EXPENSE = "expense"
    INCOME = "income"
    CORRECTION = "correction"
    QUERY_MONTH_SPENT = "query_month_spent"
    QUERY_BUDGET_REMAINING = "query_budget_remaining"
    UNKNOWN = "unknown"


@dataclass
class ParsedMessage:
    intent: Intent
    amount_cents: int | None = None
    description: str = ""
    category_slug: str | None = None


def _to_cents(raw: str) -> int:
    normalized = raw.replace(",", ".")
    return round(float(normalized) * 100)


def parse_message(text: str) -> ParsedMessage:
    text = text.strip()

    for pattern in _EXPENSE_PATTERNS:
        match = pattern.search(text)
        if match:
            desc = match.group("desc").strip()
            return ParsedMessage(
                intent=Intent.EXPENSE,
                amount_cents=-_to_cents(match.group("amount")),
                description=desc,
                category_slug=_guess_category(desc),
            )

    for pattern in _INCOME_PATTERNS:
        match = pattern.search(text)
        if match:
            desc = (match.group("desc") or "Recebimento").strip()
            return ParsedMessage(
                intent=Intent.INCOME,
                amount_cents=_to_cents(match.group("amount")),
                description=desc,
                category_slug=Category.Slug.INCOME,
            )

    match = _CORRECTION_PATTERN.match(text)
    if match:
        alias = match.group("category").strip().lower()
        category_slug = _CATEGORY_ALIASES.get(alias)
        if category_slug:
            return ParsedMessage(intent=Intent.CORRECTION, category_slug=category_slug)

    if _QUERY_MONTH_PATTERN.search(text):
        return ParsedMessage(intent=Intent.QUERY_MONTH_SPENT)

    match = _QUERY_BUDGET_PATTERN.search(text)
    if match:
        alias = match.group("category").strip().lower()
        return ParsedMessage(
            intent=Intent.QUERY_BUDGET_REMAINING, category_slug=_CATEGORY_ALIASES.get(alias)
        )

    return ParsedMessage(intent=Intent.UNKNOWN, description=text)


def _guess_category(description: str) -> str | None:
    lowered = description.lower()
    for slug, keywords in _KEYWORD_CATEGORY.items():
        if any(keyword in lowered for keyword in keywords):
            return slug
    return None
