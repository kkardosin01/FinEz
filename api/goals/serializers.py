from rest_framework import serializers

from .models import GoalContribution, SavingsGoal


class SavingsGoalSerializer(serializers.ModelSerializer):
    progress_pct = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            "id",
            "name",
            "icon",
            "target_cents",
            "saved_cents",
            "target_date",
            "completed_at",
            "progress_pct",
            "created_at",
        ]
        read_only_fields = ["saved_cents", "completed_at", "created_at"]

    def get_progress_pct(self, obj):
        if obj.target_cents <= 0:
            return 0
        return min(round(obj.saved_cents / obj.target_cents * 100), 100)

    def validate_target_cents(self, value):
        if value <= 0:
            raise serializers.ValidationError("meta deve ser maior que zero")
        return value


class GoalContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalContribution
        fields = ["id", "amount_cents", "note", "created_at"]
        read_only_fields = ["created_at"]


class ContributeSerializer(serializers.Serializer):
    amount_cents = serializers.IntegerField()
    note = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate_amount_cents(self, value):
        if value == 0:
            raise serializers.ValidationError("valor não pode ser zero")
        return value
