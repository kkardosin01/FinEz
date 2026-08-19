import pytest
from rest_framework.test import APIClient

from accounts.models import User
from transactions.categorization import categorize_provider_transaction
from transactions.models import Account, Category, CategorizationRule, Transaction

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email="teste@finez.app", password="senha-forte-123")


@pytest.fixture
def categories():
    return {
        slug: Category.objects.create(slug=slug, name_pt=slug, color_light="#000000", color_dark="#ffffff")
        for slug in [Category.Slug.GROCERIES, Category.Slug.FOOD, Category.Slug.OTHER, Category.Slug.INCOME]
    }


@pytest.fixture
def account(user):
    return Account.objects.create(user=user, type=Account.Type.MANUAL, name="Manual")


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


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


def test_update_transaction_edits_amount_description_and_date(client, user, account, categories):
    tx = Transaction.objects.create(
        user=user,
        account=account,
        category=categories[Category.Slug.FOOD],
        amount_cents=-1500,
        description="lanche",
        date="2026-08-10",
        category_source=Transaction.CategorySource.USER,
        origin=Transaction.Origin.WEB,
    )

    response = client.patch(
        f"/api/transactions/{tx.id}",
        {"amount_cents": -2000, "description": "lanche editado", "date": "2026-08-11"},
    )
    assert response.status_code == 200
    tx.refresh_from_db()
    assert tx.amount_cents == -2000
    assert tx.description == "lanche editado"
    assert str(tx.date) == "2026-08-11"


def test_update_transaction_changing_category_also_persists_other_fields(client, user, account, categories):
    """Regressão: editar categoria + outros campos juntos não pode descartar os outros campos."""
    tx = Transaction.objects.create(
        user=user,
        account=account,
        category=categories[Category.Slug.FOOD],
        amount_cents=-1500,
        description="lanche",
        date="2026-08-10",
        category_source=Transaction.CategorySource.PROVIDER,
        origin=Transaction.Origin.BANK,
    )

    response = client.patch(
        f"/api/transactions/{tx.id}",
        {"category": categories[Category.Slug.GROCERIES].id, "amount_cents": -3000, "description": "mercado"},
    )
    assert response.status_code == 200
    tx.refresh_from_db()
    assert tx.category.slug == Category.Slug.GROCERIES
    assert tx.amount_cents == -3000
    assert tx.description == "mercado"


def test_update_transaction_to_income_category_normalizes_sign(client, user, account, categories):
    tx = Transaction.objects.create(
        user=user,
        account=account,
        category=categories[Category.Slug.OTHER],
        amount_cents=-50000,
        description="salario",
        date="2026-08-05",
        category_source=Transaction.CategorySource.USER,
        origin=Transaction.Origin.WEB,
    )

    response = client.patch(f"/api/transactions/{tx.id}", {"category": categories[Category.Slug.INCOME].id})
    assert response.status_code == 200
    tx.refresh_from_db()
    assert tx.amount_cents == 50000


def test_delete_transaction_removes_it(client, user, account, categories):
    tx = Transaction.objects.create(
        user=user,
        account=account,
        category=categories[Category.Slug.FOOD],
        amount_cents=-1500,
        description="lanche",
        date="2026-08-10",
        category_source=Transaction.CategorySource.USER,
        origin=Transaction.Origin.WEB,
    )

    response = client.delete(f"/api/transactions/{tx.id}")
    assert response.status_code == 204
    assert not Transaction.objects.filter(id=tx.id).exists()


def test_cannot_edit_or_delete_another_users_transaction(user, account, categories):
    other_user = User.objects.create_user(email="outra@finez.app", password="senha-forte-123")
    tx = Transaction.objects.create(
        user=user,
        account=account,
        category=categories[Category.Slug.FOOD],
        amount_cents=-1500,
        description="lanche",
        date="2026-08-10",
        category_source=Transaction.CategorySource.USER,
        origin=Transaction.Origin.WEB,
    )

    other_client = APIClient()
    other_client.force_authenticate(user=other_user)

    assert other_client.patch(f"/api/transactions/{tx.id}", {"description": "hackeado"}).status_code == 404
    assert other_client.delete(f"/api/transactions/{tx.id}").status_code == 404
