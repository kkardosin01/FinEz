from rest_framework import serializers

from transactions.models import Category

from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    category_name = serializers.CharField(source="category.name_pt", read_only=True)
    spent_cents = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Budget
        fields = [
            "id",
            "category",
            "category_slug",
            "category_name",
            "amount_cents",
            "month",
            "spent_cents",
        ]


class BudgetUpsertItemSerializer(serializers.Serializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    amount_cents = serializers.IntegerField(min_value=0)


class BudgetUpsertSerializer(serializers.Serializer):
    month = serializers.DateField()
    budgets = BudgetUpsertItemSerializer(many=True)
