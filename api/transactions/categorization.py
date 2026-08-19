"""
Cadeia de categorização (seção 4):
categoria do agregador -> mapeamento pras 9 do sistema -> regras do usuário
(correções viram regras) -> fallback "Outros".
"""
from .models import Category, CategorizationRule

# Mapeamento das categorias do Pluggy para as 9 categorias fixas do FinEz.
# Ajustar conforme o catálogo real de categorias do Pluggy sandbox.
PROVIDER_CATEGORY_MAP = {
    "Groceries": Category.Slug.GROCERIES,
    "Restaurants and bars": Category.Slug.FOOD,
    "Food": Category.Slug.FOOD,
    "Taxi and Uber": Category.Slug.TRANSPORT,
    "Public transport": Category.Slug.TRANSPORT,
    "Subscription": Category.Slug.SUBSCRIPTIONS,
    "Health": Category.Slug.HEALTH,
    "Leisure": Category.Slug.LEISURE,
    "Housing": Category.Slug.HOUSING,
    "Salary": Category.Slug.INCOME,
    "Income": Category.Slug.INCOME,
    "Credit Card Payment": Category.Slug.CREDIT_CARD,
    "Loans and Financing": Category.Slug.LOAN,
    "Debt": Category.Slug.DEBT,
}


def categorize_provider_transaction(user, description: str, provider_category: str | None):
    """Retorna (category, category_source) para uma transação vinda do agregador."""
    rule = _match_user_rule(user, description)
    if rule:
        rule.hits_count += 1
        rule.save(update_fields=["hits_count"])
        return rule.category, "rule"

    if provider_category and provider_category in PROVIDER_CATEGORY_MAP:
        slug = PROVIDER_CATEGORY_MAP[provider_category]
        return Category.objects.get(slug=slug), "provider"

    return Category.objects.get(slug=Category.Slug.OTHER), "provider"


def categorize_free_text(user, description: str, category_source_if_matched: str = "rule"):
    """Usado pelo parser do WhatsApp/heurística antes de cair pro LLM."""
    rule = _match_user_rule(user, description)
    if rule:
        rule.hits_count += 1
        rule.save(update_fields=["hits_count"])
        return rule.category, category_source_if_matched
    return None, None


def _match_user_rule(user, description: str):
    description_lower = (description or "").lower()
    for rule in CategorizationRule.objects.filter(user=user).select_related("category"):
        if rule.match_type == CategorizationRule.MatchType.MERCHANT:
            if rule.match_value.lower() == description_lower:
                return rule
        elif rule.match_type == CategorizationRule.MatchType.DESCRIPTION_CONTAINS:
            if rule.match_value.lower() in description_lower:
                return rule
    return None


def apply_user_correction(user, transaction, new_category: Category):
    """Usuário recategoriza -> vira regra pra próximas transações parecidas."""
    transaction.category = new_category
    transaction.category_source = "user"
    transaction.save(update_fields=["category", "category_source", "updated_at"])

    CategorizationRule.objects.update_or_create(
        user=user,
        match_type=CategorizationRule.MatchType.DESCRIPTION_CONTAINS,
        match_value=transaction.description,
        defaults={"category": new_category},
    )
