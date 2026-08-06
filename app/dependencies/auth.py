import uuid
from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.exceptions import AuthenticationError
from app.core.logging import logger
from app.security.jwt import decode_access_token, mask_token
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.models.user import User


def _clean_token_string(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    token = val.strip()
    # Strip quotes recursively if present
    while (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        token = token[1:-1].strip()
    # Strip double/triple 'Bearer ' prefix if present
    while token.lower().startswith("bearer "):
        parts = token.split(" ", 1)
        token = parts[1].strip() if len(parts) > 1 else ""
        while (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            token = token[1:-1].strip()

    if token.lower() in ("null", "undefined", "none", "", "bearer"):
        return None
    return token


async def get_token_from_request(request: Request) -> str:
    # 1. Authorization header (Bearer token or raw token)
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header:
        token = _clean_token_string(auth_header)
        if token and len(token) > 15:
            logger.debug(f"[AUTH] Extracted Bearer/Header token from Authorization header: {mask_token(token)}")
            return token
        logger.warning(f"[AUTH REJECTED] Malformed or null token in Authorization header: {auth_header}")
        raise AuthenticationError("Invalid or malformed Bearer token in Authorization header.")

    # 2. Alternative custom headers (X-Access-Token, X-Auth-Token)
    alt_header = (
        request.headers.get("X-Access-Token")
        or request.headers.get("X-Auth-Token")
        or request.headers.get("x-access-token")
        or request.headers.get("x-auth-token")
    )
    token = _clean_token_string(alt_header)
    if token:
        logger.debug(f"[AUTH] Extracted token from custom header: {mask_token(token)}")
        return token

    # 3. HttpOnly Cookies (access_token, accessToken, token)
    cookie_token = (
        request.cookies.get("access_token")
        or request.cookies.get("accessToken")
        or request.cookies.get("token")
    )
    token = _clean_token_string(cookie_token)
    if token:
        logger.debug(f"[AUTH] Extracted token from HttpOnly cookie: {mask_token(token)}")
        return token

    # 4. Query Parameters (token, access_token)
    query_token = request.query_params.get("token") or request.query_params.get("access_token")
    token = _clean_token_string(query_token)
    if token:
        logger.debug(f"[AUTH] Extracted token from query parameter: {mask_token(token)}")
        return token

    logger.warning("[AUTH REJECTED] Missing authentication token in request header, cookie, or query params.")
    raise AuthenticationError("Authentication token missing. Provide Bearer token in Authorization header or HttpOnly cookie.")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> User:
    token = await get_token_from_request(request)
    logger.info(f"[AUTH ENGINE] Decoding access token: {mask_token(token)}")

    try:
        payload = decode_access_token(token)
    except AuthenticationError as exc:
        logger.warning(f"[AUTH REJECTED] Token decode failed for token {mask_token(token)}: {exc.message}")
        raise

    jti = payload.get("jti")
    user_id_str = payload.get("sub")

    if not jti or not user_id_str:
        logger.warning(f"[AUTH REJECTED] Missing required claims (jti/sub) in token: {mask_token(token)}")
        raise AuthenticationError("Invalid access token claims")

    token_repo = TokenRepository(db)
    if await token_repo.is_blacklisted(jti):
        logger.warning(f"[AUTH REJECTED] Token with jti={jti} is blacklisted/invalidated.")
        raise AuthenticationError("Access token has been logged out or invalidated")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        logger.warning(f"[AUTH REJECTED] Invalid user UUID string in token sub claim: {user_id_str}")
        raise AuthenticationError("Invalid user identifier in token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)
    if not user:
        logger.warning(f"[AUTH REJECTED] User ID {user_id_str} not found in database.")
        raise AuthenticationError("User associated with token no longer exists")

    if getattr(user, "is_deleted", False):
        logger.warning(f"[AUTH REJECTED] User {user.email} (id={user.id}) is marked as deleted.")
        raise AuthenticationError("User account has been deleted")

    if getattr(user, "is_suspended", False):
        logger.warning(f"[AUTH REJECTED] User {user.email} (id={user.id}) is suspended.")
        raise AuthenticationError("User account is suspended")

    if not getattr(user, "is_active", True):
        logger.warning(f"[AUTH REJECTED] User {user.email} (id={user.id}) is disabled/inactive.")
        raise AuthenticationError("User account is inactive or disabled")

    logger.info(f"[AUTH SUCCESS] Authenticated user: {user.email} (id={user.id}, role={user.role})")
    return user

