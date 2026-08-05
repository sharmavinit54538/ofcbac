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
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    raise AuthenticationError("Authentication token missing. Provide Bearer token or HttpOnly cookie.")


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
