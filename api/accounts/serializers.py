from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Invite, User


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "theme", "birth_date", "date_joined"]
        read_only_fields = ["id", "email", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    invite_code = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["email", "password", "name", "birth_date", "invite_code"]

    def validate_invite_code(self, value):
        try:
            invite = Invite.objects.get(code=value)
        except Invite.DoesNotExist:
            raise serializers.ValidationError("Código de convite inválido.")
        if not invite.is_valid():
            raise serializers.ValidationError("Código de convite expirado ou já usado.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        invite = Invite.objects.select_for_update().get(code=validated_data.pop("invite_code"))
        password = validated_data.pop("password")
        user = User(invited_by_code=invite, **validated_data)
        user.set_password(password)
        user.save()
        invite.used_count += 1
        invite.save(update_fields=["used_count"])
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            self.context["request"], email=attrs["email"], password=attrs["password"]
        )
        if user is None or not user.is_active:
            raise serializers.ValidationError("Email ou senha inválidos.")
        attrs["user"] = user
        return attrs
