import logging
from datetime import date

from celery import shared_task
from django.db.models import Sum
from django.utils import timezone

logger = logging.getLogger("finez")


@shared_task
def check_budget_alerts(user_id: str):
    """
    Disparado na criação de toda transação (seção 4). Verifica se algum
    orçamento cruzou 80% ou 100% e envia alerta via WhatsApp (e no app).
    """
    from accounts.models import User
    from transactions.models import Transaction
    from whatsapp.models import WhatsappLink

    from .models import Budget

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    today = date.today()
    month = date(today.year, today.month, 1)
    next_month = date(month.year + 1, 1, 1) if month.month == 12 else date(month.year, month.month + 1, 1)

    budgets = Budget.objects.filter(user=user, month=month).select_related("category")
    if not budgets.exists():
        return

    link = WhatsappLink.objects.filter(user=user, status=WhatsappLink.Status.ACTIVE).first()

    for budget in budgets:
        if budget.amount_cents <= 0:
            continue

        spent = (
            Transaction.objects.filter(
                user=user, category=budget.category, date__gte=month, date__lt=next_month, amount_cents__lt=0
            ).aggregate(total=Sum("amount_cents"))["total"]
            or 0
        )
        spent_abs = abs(spent)
        ratio = spent_abs / budget.amount_cents

        update_fields = []
        if ratio >= 1.0 and not budget.alerted_100_at:
            budget.alerted_100_at = timezone.now()
            update_fields.append("alerted_100_at")
            _notify(link, budget, spent_abs, threshold=1.0)
        elif ratio >= 0.8 and not budget.alerted_80_at:
            budget.alerted_80_at = timezone.now()
            update_fields.append("alerted_80_at")
            _notify(link, budget, spent_abs, threshold=0.8)

        if update_fields:
            budget.save(update_fields=update_fields)


def _notify(link, budget, spent_abs_cents: int, threshold: float) -> None:
    from whatsapp.sender import send_whatsapp_message

    if link:
        send_whatsapp_message(link.phone_e164, _alert_message(budget, spent_abs_cents, threshold))
    logger.info(
        "budget_alert_triggered",
        extra={"user_id": str(budget.user_id), "category_id": budget.category_id, "threshold": threshold},
    )


def _alert_message(budget, spent_abs_cents: int, threshold: float) -> str:
    category_name = budget.category.name_pt
    spent_reais = spent_abs_cents / 100
    limit_reais = budget.amount_cents / 100
    if threshold >= 1.0:
        over_reais = spent_reais - limit_reais
        return (
            f"⚠️ Orçamento de {category_name} estourou: R$ {spent_reais:.2f} de "
            f"R$ {limit_reais:.2f} (R$ {over_reais:.2f} a mais)."
        )
    return f"Você já usou 80% do orçamento de {category_name}: R$ {spent_reais:.2f} de R$ {limit_reais:.2f}."
