import base64
import hashlib
import secrets

from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone


def new_token():
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_recovery_code(code):
    normalised = "".join(character for character in (code or "").upper() if character.isalnum())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def recovery_codes(count=10):
    codes = []
    for _ in range(count):
        chunk = secrets.token_hex(4).upper()
        codes.append(f"{chunk[:4]}-{chunk[4:]}")
    return codes


def _fernet():
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value):
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value):
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def aware_now():
    return timezone.now()
