"""
Heurística de detecção de assinaturas/recorrências (seção 3 — features de produto):

Agrupa despesas por descrição normalizada (sem números, pra ignorar parcela/código)
e considera "recorrente" todo grupo com pelo menos 2 lançamentos cujo intervalo
entre datas consecutivas fica entre ~25 e ~35 dias (ciclo mensal). O valor não
entra no critério de agrupamento — assim uma assinatura que mudou de preço
(reajuste) continua sendo reconhecida como a mesma recorrência.
"""
import re
from collections import defaultdict
from datetime import date, timedelta

from transactions.models import Transaction

LOOKBACK_DAYS = 120
MIN_GAP_DAYS = 25
MAX_GAP_DAYS = 35


def normalize_description(description: str) -> str:
    text = description.lower().strip()
    text = re.sub(r"\d+", "", text)  # remove números (parcela, código de autorização etc.)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_recurring_candidates(user) -> list[tuple[str, list[Transaction]]]:
    """Retorna [(merchant_key, [transações ordenadas por data])] pra cada recorrência encontrada."""
    since = date.today() - timedelta(days=LOOKBACK_DAYS)
    transactions = (
        Transaction.objects.filter(user=user, amount_cents__lt=0, date__gte=since)
        .exclude(description="")
        .order_by("date")
    )

    groups: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        key = normalize_description(tx.description)
        if key:
            groups[key].append(tx)

    candidates = []
    for key, txs in groups.items():
        if len(txs) < 2:
            continue
        has_monthly_gap = any(
            MIN_GAP_DAYS <= (b.date - a.date).days <= MAX_GAP_DAYS for a, b in zip(txs, txs[1:])
        )
        if has_monthly_gap:
            candidates.append((key, txs))
    return candidates
