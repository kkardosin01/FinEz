from django.contrib import admin

from .models import GoalContribution, SavingsGoal


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "saved_cents", "target_cents", "target_date", "completed_at"]
    search_fields = ["user__email", "name"]


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ["user", "goal", "amount_cents", "created_at"]
    search_fields = ["user__email"]
