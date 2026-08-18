from rest_framework import serializers

from .models import Connection


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = [
            "id",
            "provider",
            "institution_name",
            "institution_logo",
            "status",
            "last_synced_at",
            "created_at",
        ]
        read_only_fields = fields


class ConnectTokenSerializer(serializers.Serializer):
    connect_token = serializers.CharField()
