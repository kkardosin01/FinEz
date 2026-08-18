import pytest

from accounts.models import User
from transactions.categorization import categorize_provider_transaction
from transactions.models import Category, CategorizationRule

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="teste@finez.app", password="senha-forte-123")


@pytest.fixture
def categories():
    return {
        slug: Category.objects.create(slug=slug, name_pt=slug, color_light="#000000", color_dark="#ffffff")
        for slug in [Category.Slug.GROCERIES, Category.Slug.FOOD, Category.Slug.OTHER]
    }


def test_provider_category_mapped_to_system_category(user, categories):
    category, source = categorize_provider_transaction(user, "Supermercado Extra", "Groceries")
    assert category.slug == Category.Slug.GROCERIES
    assert source == "provider"


def test_unknown_provider_category_falls_back_to_other(user, categories):
    category, source = categorize_provider_transaction(user, "Loja desconhecida", "Something Weird")
    assert category.slug == Category.Slug.OTHER
    assert source == "provider"


def test_user_rule_takes_precedence_over_provider_category(user, categories):
    CategorizationRule.objects.create(
        user=user,
        match_type=CategorizationRule.MatchType.DESCRIPTION_CONTAINS,
        match_value="ifood",
        category=categories[Category.Slug.FOOD],
    )
    category, source = categorize_provider_transaction(user, "iFood *Restaurante", "Groceries")
    assert category.slug == Category.Slug.FOOD
    assert source == "rule"
