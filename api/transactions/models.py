from django.db import models

from common.models import UserOwnedModel


class Category(models.Model):
    """Categorias fixas do sistema — 13 registros, seed via management command.

    Custom fica pra v2 (fora do escopo do MVP).
    """

    class Slug(models.TextChoices):
        GROCERIES = "groceries", "Mercado"
        FOOD = "food", "Alimentação"
        TRANSPORT = "transport", "Transporte"
        SUBSCRIPTIONS = "subscriptions", "Assinaturas"
        HEALTH = "health", "Saúde"
        LEISURE = "leisure", "Lazer"
        HOUSING = "housing", "Moradia"
        INCOME = "income", "Salário"
        EXTRA_INCOME = "extra_income", "Renda Extra"
        CREDIT_CARD = "credit_card", "Cartão de crédito"
        LOAN = "loan", "Empréstimo"
        DEBT = "debt", "Dívida"
        OTHER = "other", "Outros"

    id = models.SmallAutoField(primary_key=True)
    slug = models.CharField(max_length=20, choices=Slug.choices, unique=True)
    name_pt = models.CharField(max_length=50)
    color_light = models.CharField(max_length=7)
    color_dark = models.CharField(max_length=7)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name_pt


class Account(UserOwnedModel):
    """Conta bancária ou 'conta manual' (criada automaticamente por usuário)."""

    class Type(models.TextChoices):
        CHECKING = "checking", "Conta corrente"
        CREDIT_CARD = "credit_card", "Cartão de crédito"
        MANUAL = "manual", "Manual"

    connection = models.ForeignKey(
        "connections.Connection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="accounts",
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    name = models.CharField(max_length=150)
    provider_account_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "accounts"

    def __str__(self):
        return f"{self.name} ({self.user_id})"


class Transaction(UserOwnedModel):
    class CategorySource(models.TextChoices):
        PROVIDER = "provider", "Provedor"
        RULE = "rule", "Regra"
        LLM = "llm", "LLM"
        USER = "user", "Usuário"

    class Origin(models.TextChoices):
        BANK = "bank", "Banco"
        WHATSAPP = "whatsapp", "WhatsApp"
        WEB = "web", "Web"

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    # BIGINT em centavos, com sinal: saída = negativo, entrada = positivo (regras de ouro §1 e §2)
    amount_cents = models.BigIntegerField()
    description = models.CharField(max_length=255)
    date = models.DateField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="transactions"
    )
    category_source = models.CharField(max_length=10, choices=CategorySource.choices)
    origin = models.CharField(max_length=10, choices=Origin.choices)
    # Idempotência: mesma transação nunca duplica em re-sync/webhook duplicado
    provider_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    raw_provider_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "transactions"
        indexes = [
            models.Index(fields=["user", "-date"], name="tx_user_date_idx"),
            models.Index(fields=["user", "category", "date"], name="tx_user_cat_date_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["account", "provider_transaction_id"],
                condition=models.Q(provider_transaction_id__isnull=False),
                name="uniq_provider_transaction_id_per_account",
            )
        ]

    def __str__(self):
        return f"{self.description} · {self.amount_cents}"


class CategorizationRule(UserOwnedModel):
    """Correções do usuário viram regras — reduz a cauda de 'Outros' com o uso."""

    class MatchType(models.TextChoices):
        MERCHANT = "merchant", "Estabelecimento"
        DESCRIPTION_CONTAINS = "description_contains", "Descrição contém"

    match_type = models.CharField(max_length=25, choices=MatchType.choices)
    match_value = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    hits_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "categorization_rules"

    def __str__(self):
        return f"{self.match_type}:{self.match_value} -> {self.category_id}"
