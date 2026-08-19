from django.db import models

from common.models import UserOwnedModel
from transactions.models import Category


class Subscription(UserOwnedModel):
    """Assinatura/recorrência detectada automaticamente a partir do histórico de transações."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        CANCELED = "canceled", "Cancelada"

    name = models.CharField(max_length=120)
    # Descrição normalizada usada pra casar transações futuras com esta assinatura.
    merchant_key = models.CharField(max_length=160)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="subscriptions"
    )
    amount_cents = models.BigIntegerField()
    previous_amount_cents = models.BigIntegerField(null=True, blank=True)
    last_charged_at = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        db_table = "subscriptions"
        constraints = [
            models.UniqueConstraint(fields=["user", "merchant_key"], name="uniq_subscription_user_merchant")
        ]

    def __str__(self):
        return f"{self.name} · {self.amount_cents}"
