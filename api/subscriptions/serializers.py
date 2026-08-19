from rest_framework import serializers

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    category_slug = serializers.CharField(source="category.slug", read_only=True, default=None)
    category_name = serializers.CharField(source="category.name_pt", read_only=True, default=None)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "name",
            "category",
            "category_slug",
            "category_name",
            "amount_cents",
            "previous_amount_cents",
            "last_charged_at",
            "status",
            "created_at",
        ]
        read_only_fields = ["amount_cents", "previous_amount_cents", "last_charged_at", "created_at"]
