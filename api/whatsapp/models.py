import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import TimestampedModel, UserOwnedModel


def _generate_pairing_code() -> str:
    alphabet = string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


class WhatsappLink(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        ACTIVE = "active", "Ativo"
        UNLINKED = "unlinked", "Desvinculado"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)
    phone_e164 = models.CharField(max_length=20, unique=True, null=True, blank=True)
    pairing_code = models.CharField(max_length=6, default=_generate_pairing_code)
    pairing_expires_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "whatsapp_links"

    def __str__(self):
        return f"{self.user_id} · {self.status}"

    def is_pairing_code_valid(self) -> bool:
        return self.status == self.Status.PENDING and self.pairing_expires_at > timezone.now()


class WhatsappMessage(UserOwnedModel):
    class Direction(models.TextChoices):
        IN = "in", "Recebida"
        OUT = "out", "Enviada"

    direction = models.CharField(max_length=3, choices=Direction.choices)
    body = models.TextField()
    related_transaction = models.ForeignKey(
        "transactions.Transaction", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "whatsapp_messages"
        indexes = [models.Index(fields=["user", "-created_at"], name="wa_msg_user_created_idx")]

    def __str__(self):
        return f"{self.direction}: {self.body[:40]}"
