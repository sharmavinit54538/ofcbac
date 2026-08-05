import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.token_blacklist import TokenBlacklist


class TokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def blacklist_token(self, jti: str, token_type: str, user_id: Optional[uuid.UUID], expires_at: datetime) -> TokenBlacklist:
        entry = TokenBlacklist(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def is_blacklisted(self, jti: str) -> bool:
        result = await self.db.execute(
            select(TokenBlacklist).where(
                TokenBlacklist.jti == jti,
                TokenBlacklist.expires_at > datetime.now(timezone.utc)
            )
        )
        return result.scalar_one_or_none() is not None
