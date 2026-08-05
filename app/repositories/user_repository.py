import uuid
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email.ilike(email)))
        return result.scalar_one_or_none()

    async def get_by_reset_token(self, token: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.reset_password_token == token))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_onboarding_step(self, user_id: uuid.UUID, next_step: str, completed: bool = False) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(onboarding_step=next_step, onboarding_completed=completed)
        )
        await self.db.flush()

    async def update_login_metadata(self, user_id: uuid.UUID, ip_address: Optional[str] = None) -> None:
        from datetime import datetime, timezone
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc), last_login_ip=ip_address)
        )
        await self.db.flush()
