from django.conf import settings
from django.db import models

from common.models import TimestampedModel, UserOwnedModel


class Streak(TimestampedModel):
    """Contador de dias seguidos registrando gastos — um por usuário (seção 3)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_logged_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "streaks"

    def __str__(self):
        return f"{self.user_id} · {self.current_streak}d (recorde: {self.longest_streak}d)"


class Badge(UserOwnedModel):
    """Conquistas desbloqueadas — streak, orçamento em dia, meta batida (seção 3)."""

    class Slug(models.TextChoices):
        STREAK_7 = "streak_7", "🔥 7 dias seguidos"
        STREAK_30 = "streak_30", "🔥 30 dias seguidos"
        STREAK_100 = "streak_100", "🔥 100 dias seguidos"
        BUDGET_MASTER = "budget_master", "🎯 fechou o mês sem estourar orçamento"
        GOAL_ACHIEVER = "goal_achiever", "🐷 bateu uma meta de economia"

    slug = models.CharField(max_length=20, choices=Slug.choices)

    class Meta:
        db_table = "gamification_badges"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "slug"], name="uniq_badge_user_slug")]

    def __str__(self):
        return f"{self.user_id} · {self.slug}"
