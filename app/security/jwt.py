import uuid
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from app.config.settings import settings
from app.core.exceptions import AuthenticationError


def mask_token(token: Optional[str]) -> str:
    if not token:
        return "[NONE]"
    t = token.strip()
    if len(t) <= 10:
        return "***"
    return f"{t[:6]}...{t[-4:]}"


def encode_jwt(payload: Dict[str, Any], secret_key: str) -> str:
    return jwt.encode(payload, secret_key, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str, secret_key: str) -> Dict[str, Any]:
    if not token or not isinstance(token, str):
        raise AuthenticationError("Invalid authentication token format")
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True, "verify_signature": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("JWT token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid authentication token: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"Failed to decode JWT token: {str(e)}")


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": jti,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    if additional_claims:
        payload.update(additional_claims)

    token = encode_jwt(payload, settings.JWT_SECRET_KEY)
    return {
        "access_token": token,
        "jti": jti,
        "expires_at": expire
    }


def create_refresh_token(
    user_id: str,
    session_id: str,
    expires_delta: Optional[timedelta] = None
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "session_id": str(session_id),
        "jti": jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    token = encode_jwt(payload, settings.JWT_REFRESH_SECRET_KEY)
    return {
        "refresh_token": token,
        "jti": jti,
        "expires_at": expire
    }


def decode_access_token(token: str) -> Dict[str, Any]:
    payload = decode_jwt(token, settings.JWT_SECRET_KEY)
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type. Access token required.")
    return payload


def decode_refresh_token(token: str) -> Dict[str, Any]:
    payload = decode_jwt(token, settings.JWT_REFRESH_SECRET_KEY)
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type. Refresh token required.")
    return payload

