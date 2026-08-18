from django.db import models

from common.crypto import decrypt, encrypt
from common.models import UserOwnedModel


class Connection(UserOwnedModel):
    class Provider(models.TextChoices):
        PLUGGY = "pluggy", "Pluggy"

    class Status(models.TextChoices):
        SYNCING = "syncing", "Sincronizando"
        ACTIVE = "active", "Ativa"
        ERROR = "error", "Erro"
        REVOKED = "revoked", "Revogada"

    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.PLUGGY)
    provider_item_id = models.CharField(max_length=255)
    # Nunca em texto plano — Fernet, chave em env var (regras de ouro §crypto)
    access_token_encrypted = models.TextField()
    institution_name = models.CharField(max_length=150)
    institution_logo = models.URLField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SYNCING)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "connections"

    def __str__(self):
        return f"{self.institution_name} ({self.status})"

    def set_access_token(self, plaintext: str) -> None:
        self.access_token_encrypted = encrypt(plaintext)

    def get_access_token(self) -> str:
        return decrypt(self.access_token_encrypted)
