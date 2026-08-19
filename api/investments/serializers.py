from decimal import Decimal

from rest_framework import serializers

from .models import Holding

MIN_QUANTITY = Decimal("0.00000001")


class HoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = ["id", "kind", "symbol", "name", "quantity", "avg_price_cents", "created_at"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("quantidade precisa ser maior que zero")
        return value

    def validate_avg_price_cents(self, value):
        if value <= 0:
            raise serializers.ValidationError("preço médio precisa ser maior que zero")
        return value


class HoldingBuySerializer(serializers.Serializer):
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=MIN_QUANTITY)
    price_cents = serializers.IntegerField(min_value=1)


class HoldingSellSerializer(serializers.Serializer):
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=MIN_QUANTITY)
