from django.db import models

from common.models import UserOwnedModel


class Holding(UserOwnedModel):
    """Posição de investimento lançada manualmente pelo usuário (seção 3 —
    carteira/deep-dive de investimentos). Sem integração com corretora: o
    usuário registra o que tem, a gente só busca a cotação atual."""

    class Kind(models.TextChoices):
        STOCK = "stock", "Ação"
        FII = "fii", "FII"
        CRYPTO = "crypto", "Cripto"

    kind = models.CharField(max_length=10, choices=Kind.choices)
    # ticker (ações/FIIs, ex: PETR4) ou id da CoinGecko (cripto, ex: bitcoin)
    symbol = models.CharField(max_length=30)
    name = models.CharField(max_length=120, blank=True, default="")
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    avg_price_cents = models.BigIntegerField()  # preço médio de compra, por unidade

    class Meta:
        db_table = "investment_holdings"
        constraints = [
            models.UniqueConstraint(fields=["user", "kind", "symbol"], name="uniq_holding_user_kind_symbol")
        ]

    def __str__(self):
        return f"{self.user_id} · {self.symbol} · {self.quantity}"
