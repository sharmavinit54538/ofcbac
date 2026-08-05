import hashlib
import os
import secrets


def hash_password(password: str) -> str:
    """
    Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a secure salt.
    Format: pbkdf2:sha256:100000$salt$hash
    """
    salt = secrets.token_hex(16)
    iterations = 100000
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    key_hex = key.hex()
    return f"pbkdf2:sha256:{iterations}${salt}${key_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored hashed password."""
    try:
        if not hashed_password or "$" not in hashed_password:
            return False
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False

        header, salt, expected_hash = parts
        algorithm, sub_algo, iterations = header.split(":")
        iterations = int(iterations)

        key = hashlib.pbkdf2_hmac(
            sub_algo,
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        )
        actual_hash = key.hex()
        return secrets.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False
