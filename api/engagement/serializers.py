from rest_framework import serializers

from .models import Badge, Streak


class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = ["current_streak", "longest_streak", "last_logged_date"]


class BadgeSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_slug_display", read_only=True)

    class Meta:
        model = Badge
        fields = ["id", "slug", "label", "created_at"]
