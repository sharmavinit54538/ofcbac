import secrets
import hmac
import hashlib
from app.config.settings import settings

def generate_csrf_token() -> str:
    """Generates a secure random CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(header_token: str, cookie_token: str) -> bool:
    """Validates double submit CSRF token."""
    if not header_token or not cookie_token:
        return False
    return secrets.compare_digest(header_token, cookie_token)
