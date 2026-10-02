import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

_PREFIX = "enc:v1:"


def _fernet() -> Fernet:
    digest = hashlib.sha256(get_settings().secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    if not value or value.startswith(_PREFIX):
        return value
    token = _fernet().encrypt(value.encode()).decode()
    return f"{_PREFIX}{token}"


def decrypt_secret(value: str) -> str:
    if not value or not value.startswith(_PREFIX):
        return value
    try:
        return _fernet().decrypt(value[len(_PREFIX) :].encode()).decode()
    except InvalidToken:
        return value
