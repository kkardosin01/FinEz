import pytest
from cryptography.fernet import Fernet, InvalidToken

from common.crypto import decrypt, encrypt


def test_encrypt_decrypt_round_trip(settings):
    settings.FERNET_KEY = Fernet.generate_key().decode()
    ciphertext = encrypt("token-secreto-do-pluggy")
    assert ciphertext != "token-secreto-do-pluggy"
    assert decrypt(ciphertext) == "token-secreto-do-pluggy"


def test_encrypt_without_key_configured_raises(settings):
    settings.FERNET_KEY = ""
    with pytest.raises(RuntimeError):
        encrypt("token-secreto-do-pluggy")


def test_decrypt_with_wrong_key_fails(settings):
    settings.FERNET_KEY = Fernet.generate_key().decode()
    ciphertext = encrypt("token-secreto-do-pluggy")

    settings.FERNET_KEY = Fernet.generate_key().decode()
    with pytest.raises(InvalidToken):
        decrypt(ciphertext)
