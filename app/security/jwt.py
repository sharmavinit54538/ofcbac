import hmac
import hashlib
import json
import base64
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from app.config.settings import settings
from app.core.exceptions import AuthenticationError


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def encode_jwt(payload: Dict[str, Any], secret_key: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    header_b64 = _base64url_encode(header_json)
    payload_b64 = _base64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt(token: str, secret_key: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthenticationError("Invalid JWT token format")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_sig = _base64url_decode(signature_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise AuthenticationError("Invalid JWT signature")

    payload_json = _base64url_decode(payload_b64)
    payload = json.loads(payload_json.decode("utf-8"))

    exp = payload.get("exp")
    if exp:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if now_ts > exp:
            raise AuthenticationError("JWT token has expired")

    return payload


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
