"""IAS Issuer Authorization service: accounts, roles, and access tokens (NFR-01)."""

import hashlib
import secrets


def hash_password(password: str) -> str:
    """scrypt with a random 16-byte salt, stored as scrypt$<salt hex>$<digest hex>."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"
