from transactions.models import Category
from whatsapp.parser import Intent, parse_message


def test_parse_expense_with_keyword_category():
    parsed = parse_message("gastei 25,90 no mercado")
    assert parsed.intent == Intent.EXPENSE
    assert parsed.amount_cents == -2590
    assert parsed.category_slug == Category.Slug.GROCERIES


def test_parse_expense_without_known_keyword():
    parsed = parse_message("gastei 10 na padoca")
    assert parsed.intent == Intent.EXPENSE
    assert parsed.amount_cents == -1000
    assert parsed.category_slug is None


def test_parse_income():
    parsed = parse_message("recebi 1500 do freela")
    assert parsed.intent == Intent.INCOME
    assert parsed.amount_cents == 150000
    assert parsed.category_slug == Category.Slug.INCOME


def test_parse_correction():
    parsed = parse_message("era transporte")
    assert parsed.intent == Intent.CORRECTION
    assert parsed.category_slug == Category.Slug.TRANSPORT


def test_parse_query_month_spent():
    parsed = parse_message("quanto gastei esse mês?")
    assert parsed.intent == Intent.QUERY_MONTH_SPENT


def test_parse_unknown_falls_back():
    parsed = parse_message("oi tudo bem?")
    assert parsed.intent == Intent.UNKNOWN
