from rest_framework import serializers

from .categorization import apply_user_correction
from .models import Account, Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "name_pt", "color_light", "color_dark"]


class TransactionSerializer(serializers.ModelSerializer):
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "account_name",
            "amount_cents",
            "description",
            "date",
            "category",
            "category_slug",
            "category_source",
            "origin",
            "created_at",
        ]
        read_only_fields = ["category_source", "origin", "created_at"]

    def update(self, instance, validated_data):
        new_category = validated_data.get("category")
        if new_category and new_category != instance.category:
            apply_user_correction(self.context["request"].user, instance, new_category)
            instance.refresh_from_db()
            return instance
        return super().update(instance, validated_data)


class ManualTransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["amount_cents", "description", "date", "category"]

    def validate(self, attrs):
        category = attrs.get("category")
        amount_cents = attrs.get("amount_cents")
        if category is not None and amount_cents is not None:
            income_slugs = {Category.Slug.INCOME, Category.Slug.EXTRA_INCOME}
            if category.slug in income_slugs and amount_cents < 0:
                # Salário e Renda Extra são sempre dinheiro entrando na conta
                attrs["amount_cents"] = abs(amount_cents)
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        manual_account, _ = Account.objects.get_or_create(
            user=user,
            type=Account.Type.MANUAL,
            defaults={"name": "Lançamentos manuais"},
        )
        return Transaction.objects.create(
            user=user,
            account=manual_account,
            origin=Transaction.Origin.WEB,
            category_source=Transaction.CategorySource.USER,
            **validated_data,
        )
