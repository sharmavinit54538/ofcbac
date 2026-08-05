import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, session: Session) -> Session:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        result = await self.db.execute(
            select(Session).where(Session.id == session_id, Session.is_revoked.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, token_hash: str) -> Optional[Session]:
        result = await self.db.execute(
            select(Session).where(Session.refresh_token_hash == token_hash, Session.is_revoked.is_(False))
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(is_revoked=True)
        )
        await self.db.flush()

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.user_id == user_id, Session.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        await self.db.flush()

    async def update_session_token(self, session_id: uuid.UUID, new_token_hash: str, new_expires_at: datetime) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(
                refresh_token_hash=new_token_hash,
                expires_at=new_expires_at,
                last_used_at=datetime.now(timezone.utc)
            )
        )
        await self.db.flush()
