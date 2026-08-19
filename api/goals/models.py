from django.db import models

from common.models import UserOwnedModel


class SavingsGoal(UserOwnedModel):
    """Meta de economia ("cofrinho"): guarda um alvo e o total já guardado."""

    name = models.CharField(max_length=120)
    icon = models.CharField(max_length=8, default="🐷")
    target_cents = models.BigIntegerField()
    saved_cents = models.BigIntegerField(default=0)
    target_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "savings_goals"

    def __str__(self):
        return f"{self.name} ({self.saved_cents}/{self.target_cents})"


class GoalContribution(UserOwnedModel):
    """Histórico de aportes/resgates de uma meta. Valor positivo = aporte, negativo = resgate."""

    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name="contributions")
    amount_cents = models.BigIntegerField()
    note = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        db_table = "goal_contributions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.goal_id} · {self.amount_cents}"
