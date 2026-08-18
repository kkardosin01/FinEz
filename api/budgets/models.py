from django.db import models

from common.models import UserOwnedModel
from transactions.models import Category


class Budget(UserOwnedModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    amount_cents = models.BigIntegerField()  # positivo — limite do mês
    month = models.DateField()  # sempre dia 1
    # Evita reenviar o mesmo alerta a cada nova transação do mês
    alerted_80_at = models.DateTimeField(null=True, blank=True)
    alerted_100_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "budgets"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "month"], name="uniq_budget_user_category_month"
            )
        ]

    def __str__(self):
        return f"{self.category_id} · {self.month} · {self.amount_cents}"
