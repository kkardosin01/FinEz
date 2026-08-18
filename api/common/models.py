import uuid

from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    """created_at / updated_at em tudo (regra de ouro nº 4)."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserOwnedManager(models.Manager):
    """Isolamento de dados por usuário: nunca consultar sem escopo de user."""

    def for_user(self, user):
        return self.get_queryset().filter(user=user)


class UserOwnedModel(TimestampedModel):
    """Todo registro tem user_id (regra de ouro nº 3)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    objects = UserOwnedManager()

    class Meta:
        abstract = True


class WebhookEvent(TimestampedModel):
    """
    Fila de auditoria de webhooks (seção 4): o endpoint só valida a assinatura,
    grava o evento bruto e responde 200 em milissegundos; o Celery processa.
    """

    class Source(models.TextChoices):
        PLUGGY = "pluggy", "Pluggy"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSED = "processed", "Processado"
        FAILED = "failed", "Falhou"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=20, choices=Source.choices)
    payload = models.JSONField()
    signature_valid = models.BooleanField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "webhook_events"
        indexes = [
            models.Index(
                fields=["status"],
                name="webhook_pending_idx",
                condition=models.Q(status="pending"),
            ),
        ]

    def __str__(self):
        return f"{self.source}:{self.status}"
