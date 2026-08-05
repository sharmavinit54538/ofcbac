import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.session import Session
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.services.audit_service import AuditService
from app.security.hashing import hash_password
from app.security.jwt import create_access_token, create_refresh_token
from app.security.tokens import hash_token, secrets
from app.core.exceptions import AuthenticationError


class OAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.audit_service = AuditService(db)

    async def google_login(
        self,
        credential: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        if not credential:
            raise AuthenticationError("Invalid Google credential token")

        email = f"google_user_{credential[:8]}@example.com" if not "@" in credential else credential
        first_name = "Google"
        last_name = "User"

        user = await self.user_repo.get_by_email(email)
        if not user:
            random_pw = hash_password(secrets.token_urlsafe(32))
            new_user = User(
                email=email.lower(),
                hashed_password=random_pw,
                first_name=first_name,
                last_name=last_name,
                company_name="Google SSO Company",
                role="Organization Admin",
                is_verified=True,
                onboarding_completed=False,
                onboarding_step="company"
            )
            user = await self.user_repo.create(new_user)
            await self.audit_service.log_event("GOOGLE_SSO_REGISTER", user_id=user.id, ip_address=ip_address)
        else:
            await self.audit_service.log_event("GOOGLE_SSO_LOGIN", user_id=user.id, ip_address=ip_address)

        session_id = uuid.uuid4()
        refresh_data = create_refresh_token(user_id=str(user.id), session_id=str(session_id))
        refresh_hash = hash_token(refresh_data["refresh_token"])

        session_entry = Session(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device="Google OAuth Client",
            browser=user_agent or "Google SSO",
            ip_address=ip_address,
            is_revoked=False,
            expires_at=refresh_data["expires_at"]
        )
        await self.session_repo.create_session(session_entry)
        access_data = create_access_token(user_id=str(user.id), role=user.role)

        await self.db.commit()

        next_step = "/dashboard" if user.onboarding_completed else "/onboarding/status"

        return {
            "user": user,
            "tokens": {
                "access_token": access_data["access_token"],
                "refresh_token": refresh_data["refresh_token"],
                "token_type": "bearer"
            },
            "is_verified": user.is_verified,
            "onboarding_completed": user.onboarding_completed,
            "next_step": next_step
        }

    async def okta_login(
        self,
        code: str,
        redirect_uri: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        if not code:
            raise AuthenticationError("Invalid Okta authorization code")

        email = f"okta_user_{code[:8]}@enterprise.com"
        user = await self.user_repo.get_by_email(email)
        if not user:
            random_pw = hash_password(secrets.token_urlsafe(32))
            new_user = User(
                email=email.lower(),
                hashed_password=random_pw,
                first_name="Okta",
                last_name="SSO User",
                company_name="Enterprise Okta Organization",
                role="Organization Admin",
                is_verified=True,
                onboarding_completed=False,
                onboarding_step="company"
            )
            user = await self.user_repo.create(new_user)
            await self.audit_service.log_event("OKTA_SSO_REGISTER", user_id=user.id, ip_address=ip_address)
        else:
            await self.audit_service.log_event("OKTA_SSO_LOGIN", user_id=user.id, ip_address=ip_address)

        session_id = uuid.uuid4()
        refresh_data = create_refresh_token(user_id=str(user.id), session_id=str(session_id))
        refresh_hash = hash_token(refresh_data["refresh_token"])

        session_entry = Session(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device="Okta SSO Client",
            browser=user_agent or "Okta OIDC",
            ip_address=ip_address,
            is_revoked=False,
            expires_at=refresh_data["expires_at"]
        )
        await self.session_repo.create_session(session_entry)
        access_data = create_access_token(user_id=str(user.id), role=user.role)

        await self.db.commit()

        next_step = "/dashboard" if user.onboarding_completed else "/onboarding/status"

        return {
            "user": user,
            "tokens": {
                "access_token": access_data["access_token"],
                "refresh_token": refresh_data["refresh_token"],
                "token_type": "bearer"
            },
            "is_verified": user.is_verified,
            "onboarding_completed": user.onboarding_completed,
            "next_step": next_step
        }
