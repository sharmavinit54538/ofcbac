import uuid
from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.exceptions import AuthenticationError
from app.security.jwt import decode_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.models.user import User


async def get_token_from_request(request: Request) -> str:
    # 1. Authorization header (Bearer token or raw token)
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header:
        auth_header = auth_header.strip()
        if auth_header.lower().startswith("bearer "):
            parts = auth_header.split(" ", 1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()
        elif " " not in auth_header and len(auth_header) > 20:
            return auth_header

    # 2. Alternative custom headers (X-Access-Token, X-Auth-Token)
    alt_header = (
        request.headers.get("X-Access-Token")
        or request.headers.get("X-Auth-Token")
        or request.headers.get("x-access-token")
    )
    if alt_header and alt_header.strip():
        return alt_header.strip()

    # 3. HttpOnly Cookies (access_token, accessToken, token)
    cookie_token = (
        request.cookies.get("access_token")
        or request.cookies.get("accessToken")
        or request.cookies.get("token")
    )
    if cookie_token and cookie_token.strip():
        return cookie_token.strip()

    # 4. Query Parameters (token, access_token)
    query_token = request.query_params.get("token") or request.query_params.get("access_token")
    if query_token and query_token.strip():
        return query_token.strip()

    raise AuthenticationError("Authentication token missing. Provide Bearer token in Authorization header or HttpOnly cookie.")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> User:
    token = await get_token_from_request(request)
    payload = decode_access_token(token)

    jti = payload.get("jti")
    user_id_str = payload.get("sub")

    if not jti or not user_id_str:
        raise AuthenticationError("Invalid access token claims")

    token_repo = TokenRepository(db)
    if await token_repo.is_blacklisted(jti):
        raise AuthenticationError("Access token has been logged out or invalidated")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id_str))
    if not user:
        raise AuthenticationError("User associated with token no longer exists")

    return user
