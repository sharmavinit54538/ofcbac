import hashlib
import random
import secrets
import string


def hash_token(token: str) -> str:
    """Hashes a raw token string (e.g., refresh token) using SHA-256 for secure DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_otp(length: int = 6) -> str:
    """Generates a numeric OTP code for email verification."""
    return "".join(random.choices(string.digits, k=length))


def generate_reset_token() -> str:
    """Generates a high-entropy URL-safe password reset token."""
    return secrets.token_urlsafe(48)
