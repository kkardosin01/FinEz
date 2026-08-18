"""Criptografia simétrica (Fernet) para tokens de terceiros (regra de ouro §5)."""
from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    if not settings.FERNET_KEY:
        raise RuntimeError(
            "FERNET_KEY não configurada. Gere uma com "
            "`python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`"
        )
    return Fernet(settings.FERNET_KEY)


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()
