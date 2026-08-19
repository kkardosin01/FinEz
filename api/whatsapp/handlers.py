"""
Lógica de resposta do bot (seção 2 — regras de design da conversa):
- toda mensagem recebe resposta em segundos
- confirmações curtas, sem tom moralista
- nunca duas perguntas na mesma mensagem
"""
import logging
from datetime import date

from django.db.models import Sum
from django.utils import timezone

from budgets.models import Budget
from budgets.tasks import check_budget_alerts
from engagement.services import record_activity
from engagement.tasks import check_spending_anomaly
from subscriptions.tasks import detect_subscriptions
from transactions.categorization import apply_user_correction, categorize_free_text
from transactions.models import Account, Category, Transaction

from .llm_fallback import parse_with_llm
from .parser import Intent, parse_message

logger = logging.getLogger("finez")

HELP_MESSAGE = "não entendi 🤔 tenta assim: *gastei 30 no mercado*"


def handle_incoming_message(user, text: str) -> str:
    parsed = parse_message(text)
    if parsed.intent == Intent.UNKNOWN:
        parsed = parse_with_llm(text)

    if parsed.intent == Intent.EXPENSE:
        return _handle_transaction(user, parsed, origin_label="gasto")
    if parsed.intent == Intent.INCOME:
        return _handle_transaction(user, parsed, origin_label="recebimento")
    if parsed.intent == Intent.CORRECTION:
        return _handle_correction(user, parsed)
    if parsed.intent == Intent.QUERY_MONTH_SPENT:
        return _handle_query_month_spent(user)
    if parsed.intent == Intent.QUERY_BUDGET_REMAINING:
        return _handle_query_budget_remaining(user, parsed)

    return HELP_MESSAGE


def _handle_transaction(user, parsed, origin_label: str) -> str:
    manual_account, _ = Account.objects.get_or_create(
        user=user, type=Account.Type.MANUAL, defaults={"name": "Lançamentos manuais"}
    )

    # Cadeia de categorização: regra do usuário -> palavra-chave da heurística -> Outros
    rule_category, rule_source = categorize_free_text(user, parsed.description)
    if rule_category:
        category, source = rule_category, rule_source
    elif parsed.category_slug:
        category = Category.objects.get(slug=parsed.category_slug)
        source = Transaction.CategorySource.RULE
    else:
        # Categoria não inferida entra como "Outros", nunca bloqueia o lançamento (seção 2)
        category = Category.objects.get(slug=Category.Slug.OTHER)
        source = Transaction.CategorySource.RULE

    transaction = Transaction.objects.create(
        user=user,
        account=manual_account,
        amount_cents=parsed.amount_cents,
        description=parsed.description or origin_label,
        date=date.today(),
        category=category,
        category_source=source,
        origin=Transaction.Origin.WHATSAPP,
    )
    check_budget_alerts.delay(str(user.id))
    detect_subscriptions.delay(str(user.id))
    check_spending_anomaly.delay(str(user.id))
    new_badges = record_activity(user) if transaction.amount_cents < 0 else []
    return _format_confirmation(transaction, new_badges)


def _format_confirmation(transaction: Transaction, new_badges=None) -> str:
    value = abs(transaction.amount_cents) / 100
    category_name = transaction.category.name_pt
    message = (
        f"✓ R$ {value:.2f} · {category_name} · hoje\n"
        "errou a categoria? manda *era <categoria>*"
    )
    for badge in new_badges or []:
        message += f"\n🏆 {badge.get_slug_display()}!"
    return message


def _handle_correction(user, parsed) -> str:
    last_transaction = (
        Transaction.objects.filter(user=user, origin=Transaction.Origin.WHATSAPP)
        .order_by("-created_at")
        .first()
    )
    if not last_transaction:
        return "não achei nenhum lançamento recente pra corrigir 🤔"

    new_category = Category.objects.filter(slug=parsed.category_slug).first()
    if not new_category:
        return HELP_MESSAGE

    apply_user_correction(user, last_transaction, new_category)
    return f"beleza, recategorizado pra {new_category.name_pt} ✓"


def _handle_query_month_spent(user) -> str:
    today = timezone.now().date()
    month_start = date(today.year, today.month, 1)
    total = (
        Transaction.objects.filter(user=user, date__gte=month_start, date__lte=today, amount_cents__lt=0)
        .aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    return f"você gastou R$ {abs(total) / 100:.2f} esse mês até agora"


def _handle_query_budget_remaining(user, parsed) -> str:
    if not parsed.category_slug:
        return "de qual categoria? tenta *quanto sobrou do orçamento de lazer*"

    today = timezone.now().date()
    month_start = date(today.year, today.month, 1)
    budget = Budget.objects.filter(
        user=user, category__slug=parsed.category_slug, month=month_start
    ).select_related("category").first()
    if not budget:
        return "você ainda não tem orçamento definido pra essa categoria"

    spent = (
        Transaction.objects.filter(
            user=user, category=budget.category, date__gte=month_start, date__lte=today, amount_cents__lt=0
        ).aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    remaining = budget.amount_cents - abs(spent)
    if remaining < 0:
        return f"o orçamento de {budget.category.name_pt} já estourou em R$ {abs(remaining) / 100:.2f}"
    return f"sobrou R$ {remaining / 100:.2f} do orçamento de {budget.category.name_pt}"
