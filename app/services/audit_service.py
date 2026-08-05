import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: AsyncSession):
        self.audit_repo = AuditRepository(db)

    async def log_event(
        self,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        resource: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[str] = None
    ):
        return await self.audit_repo.log_action(
            action=action,
            user_id=user_id,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details
        )
