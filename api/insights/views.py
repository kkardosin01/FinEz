"""
Insights automáticos (Fase 1 — sem IA generativa): compara o mês corrente
com o mês anterior e gera frases determinísticas em português a partir de
templates condicionais. Tudo calculado no backend (front não soma nada),
seguindo o mesmo padrão do /api/summary.
"""
from datetime import date

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.models import Transaction
from transactions.views import _month_bounds


def _shift_month(start: date, delta: int) -> date:
    month_index = start.month - 1 + delta
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _pct_change(prev_cents: int, current_cents: int) -> float | None:
    """% de variação em valor absoluto. `None` quando não há base de comparação
    (categoria não existia no mês anterior) — evita dividir por zero."""
    prev_abs = abs(prev_cents)
    current_abs = abs(current_cents)
    if prev_abs == 0:
        return None
    return round((current_abs - prev_abs) / prev_abs * 100, 1)


def _format_brl(cents: int) -> str:
    value = abs(cents) / 100
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _category_change_summary(category: dict | None) -> dict | None:
    if not category:
        return None
    return {
        "category_name": category["category_name"],
        "change_pct_vs_prev_month": category["change_pct_vs_prev_month"],
    }


def generate_insight_messages(data: dict) -> list[str]:
    """Templates condicionais determinísticos — só gera frase quando a variação
    é grande o bastante pra valer a pena (evita ruído com oscilações pequenas)."""
    messages: list[str] = []

    increase = data.get("biggest_increase_category")
    if increase and increase["change_pct_vs_prev_month"] is not None and increase["change_pct_vs_prev_month"] > 15:
        messages.append(
            f"Você gastou {increase['change_pct_vs_prev_month']:.0f}% a mais em "
            f"{increase['category_name']} esse mês comparado ao mês passado."
        )

    decrease = data.get("biggest_decrease_category")
    if decrease and decrease["change_pct_vs_prev_month"] is not None and decrease["change_pct_vs_prev_month"] < -15:
        messages.append(
            f"Parabéns! Você gastou {abs(decrease['change_pct_vs_prev_month']):.0f}% a menos em "
            f"{decrease['category_name']} esse mês."
        )

    total_change = data.get("total_expense_change_pct")
    if total_change is not None and abs(total_change) > 10:
        direction = "a mais" if total_change > 0 else "a menos"
        messages.append(f"No total, você gastou {abs(total_change):.0f}% {direction} do que no mês passado.")

    biggest_tx = data.get("biggest_single_transaction")
    if biggest_tx:
        messages.append(
            f'Sua maior compra do mês foi "{biggest_tx["description"]}" — {_format_brl(biggest_tx["amount_cents"])}.'
        )

    if not messages:
        messages.append("Sem dados suficientes ainda pra gerar insights esse mês.")

    return messages


class InsightsView(APIView):
    """GET /api/insights?month= — comparativo com o mês anterior, sem chamada de IA."""

    def get(self, request):
        month = request.query_params.get("month")
        start, end = _month_bounds(month)
        prev_start = _shift_month(start, -1)
        prev_end = start

        qs = Transaction.objects.filter(user=request.user, date__gte=start, date__lt=end)
        prev_qs = Transaction.objects.filter(user=request.user, date__gte=prev_start, date__lt=prev_end)

        expense_qs = qs.filter(amount_cents__lt=0)
        prev_expense_qs = prev_qs.filter(amount_cents__lt=0)

        total_expense_cents = expense_qs.aggregate(s=Sum("amount_cents"))["s"] or 0
        prev_total_expense_cents = prev_expense_qs.aggregate(s=Sum("amount_cents"))["s"] or 0

        days_in_month = (end - start).days
        daily_avg_expense_cents = round(total_expense_cents / days_in_month) if days_in_month else 0

        by_category = list(
            expense_qs.values("category__slug", "category__name_pt")
            .annotate(total_cents=Sum("amount_cents"))
            .order_by("total_cents")
        )
        prev_by_category = {
            row["category__slug"]: row["total_cents"]
            for row in prev_expense_qs.values("category__slug").annotate(total_cents=Sum("amount_cents"))
        }

        top_categories = []
        for row in by_category:
            slug = row["category__slug"]
            prev_cents = prev_by_category.get(slug, 0)
            pct_of_total = (abs(row["total_cents"]) / abs(total_expense_cents) * 100) if total_expense_cents else 0
            top_categories.append(
                {
                    "category_slug": slug,
                    "category_name": row["category__name_pt"],
                    "total_cents": row["total_cents"],
                    "pct_of_total": round(pct_of_total, 1),
                    "change_pct_vs_prev_month": _pct_change(prev_cents, row["total_cents"]),
                }
            )

        categories_with_change = [c for c in top_categories if c["change_pct_vs_prev_month"] is not None]
        biggest_increase = (
            max(categories_with_change, key=lambda c: c["change_pct_vs_prev_month"])
            if categories_with_change
            else None
        )
        biggest_decrease = (
            min(categories_with_change, key=lambda c: c["change_pct_vs_prev_month"])
            if categories_with_change
            else None
        )

        biggest_tx = expense_qs.select_related("category").order_by("amount_cents").first()
        biggest_single_transaction = (
            {
                "description": biggest_tx.description,
                "amount_cents": biggest_tx.amount_cents,
                "date": biggest_tx.date,
                "category_name": biggest_tx.category.name_pt,
            }
            if biggest_tx
            else None
        )

        data = {
            "month": start.strftime("%Y-%m"),
            "previous_month": prev_start.strftime("%Y-%m"),
            "total_expense_cents": total_expense_cents,
            "total_expense_change_pct": _pct_change(prev_total_expense_cents, total_expense_cents),
            "daily_avg_expense_cents": daily_avg_expense_cents,
            "top_categories": top_categories[:5],
            "biggest_increase_category": _category_change_summary(biggest_increase),
            "biggest_decrease_category": _category_change_summary(biggest_decrease),
            "biggest_single_transaction": biggest_single_transaction,
        }
        data["messages"] = generate_insight_messages(data)

        return Response(data)
