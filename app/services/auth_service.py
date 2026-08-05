import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.session import Session
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.token_repository import TokenRepository
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.security.hashing import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token, decode_refresh_token, decode_access_token
from app.security.tokens import hash_token, generate_otp, generate_reset_token
from app.core.exceptions import (
    AuthenticationError, ConflictError, NotFoundError, ValidationError
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.token_repo = TokenRepository(db)
        self.audit_service = AuditService(db)

    async def register(
        self,
        register_data: Any,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        existing_user = await self.user_repo.get_by_email(register_data.email)
        if existing_user:
            raise ConflictError("User with this email already exists")

        otp_code = generate_otp(6)
        otp_expires = datetime.now(timezone.utc) + timedelta(minutes=15)

        hashed_pw = hash_password(register_data.password)

        new_user = User(
            email=register_data.email.lower(),
            hashed_password=hashed_pw,
            first_name=register_data.first_name,
            last_name=register_data.last_name,
            phone=register_data.phone,
            company_name=register_data.company_name,
            role="Organization Admin",
            is_verified=False,
            onboarding_completed=False,
            onboarding_step="company",
            verification_otp=otp_code,
            verification_otp_expires_at=otp_expires
        )

        user = await self.user_repo.create(new_user)

        session_id = uuid.uuid4()
        refresh_data = create_refresh_token(user_id=str(user.id), session_id=str(session_id))
        refresh_hash = hash_token(refresh_data["refresh_token"])

        session_entry = Session(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device="Web/Mobile Client",
            browser=user_agent or "Unknown Browser",
            ip_address=ip_address,
            is_revoked=False,
            expires_at=refresh_data["expires_at"]
        )
        await self.session_repo.create_session(session_entry)

        access_data = create_access_token(user_id=str(user.id), role=user.role)

        await self.audit_service.log_event(
            action="USER_REGISTERED",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"User {user.email} registered. Verification OTP generated."
        )

        await self.db.commit()

        # Dispatch HTML email verification OTP code to user
        await EmailService.send_verification_email(
            to_email=user.email,
            first_name=user.first_name,
            otp_code=otp_code
        )

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
            "next_step": next_step,
            "otp_debug": otp_code
        }

    async def verify_email(self, email: str, otp: str) -> bool:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundError("User not found")

        if user.is_verified:
            return True

        if not user.verification_otp or user.verification_otp != otp:
            raise ValidationError("Invalid verification OTP code")

        if user.verification_otp_expires_at:
            expires_at = user.verification_otp_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise ValidationError("Verification OTP has expired")

        user.is_verified = True
        user.verification_otp = None
        user.verification_otp_expires_at = None
        await self.audit_service.log_event(
            action="EMAIL_VERIFIED",
            user_id=user.id,
            details=f"User {user.email} verified email successfully."
        )
        await self.db.commit()
        return True

    async def resend_verification_otp(self, email: str) -> Dict[str, Any]:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return {
                "message": "If the email is registered and not verified, a new verification code has been sent.",
                "otp_debug": None
            }

        if user.is_verified:
            return {
                "message": "Email is already verified.",
                "otp_debug": None
            }

        new_otp = generate_otp()
        user.verification_otp = new_otp
        user.verification_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        await self.audit_service.log_event(
            action="RESEND_VERIFICATION_OTP_REQUESTED",
            user_id=user.id,
            details=f"New verification OTP generated for {user.email}"
        )
        await self.db.commit()

        # Send HTML email verification OTP
        await EmailService.send_verification_email(
            to_email=user.email,
            first_name=user.first_name,
            otp_code=new_otp
        )

        return {
            "message": "A new verification code has been sent to your email address.",
            "otp_debug": new_otp
        }

    async def login(
        self,
        login_data: Any,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            await self.audit_service.log_event(
                action="LOGIN_FAILED",
                ip_address=ip_address,
                user_agent=user_agent,
                status="FAILURE",
                details=f"Failed login attempt for email: {login_data.email}"
            )
            await self.db.commit()
            raise AuthenticationError("Invalid email or password")

        if not verify_password(login_data.password, user.hashed_password):
            await self.audit_service.log_event(
                action="LOGIN_FAILED",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="FAILURE",
                details="Invalid password provided"
            )
            await self.db.commit()
            raise AuthenticationError("Invalid email or password")

        if not user.is_verified:
            raise AuthenticationError("Email is not verified. Please verify your email before logging in.")

        await self.user_repo.update_login_metadata(user.id, ip_address)

        session_id = uuid.uuid4()
        refresh_data = create_refresh_token(user_id=str(user.id), session_id=str(session_id))
        refresh_hash = hash_token(refresh_data["refresh_token"])

        session_entry = Session(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device="Desktop/Mobile",
            browser=user_agent or "Browser",
            ip_address=ip_address,
            is_revoked=False,
            expires_at=refresh_data["expires_at"]
        )
        await self.session_repo.create_session(session_entry)

        access_data = create_access_token(user_id=str(user.id), role=user.role)

        await self.audit_service.log_event(
            action="LOGIN_SUCCESS",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"User {user.email} logged in successfully."
        )

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

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        payload = decode_refresh_token(refresh_token)
        user_id_str = payload.get("sub")
        session_id_str = payload.get("session_id")

        if not user_id_str or not session_id_str:
            raise AuthenticationError("Invalid refresh token payload")

        session_id = uuid.UUID(session_id_str)
        token_hash = hash_token(refresh_token)

        session = await self.session_repo.get_by_id(session_id)
        if not session or session.is_revoked:
            await self.session_repo.revoke_all_user_sessions(uuid.UUID(user_id_str))
            await self.db.commit()
            raise AuthenticationError("Refresh token has been revoked or reused. All sessions invalidated.")

        if session.refresh_token_hash != token_hash:
            await self.session_repo.revoke_all_user_sessions(uuid.UUID(user_id_str))
            await self.db.commit()
            raise AuthenticationError("Refresh token reuse detected. Replay attack prevented. All sessions invalidated.")

        user = await self.user_repo.get_by_id(uuid.UUID(user_id_str))
        if not user:
            raise NotFoundError("User not found")

        new_refresh_data = create_refresh_token(user_id=str(user.id), session_id=str(session.id))
        new_hash = hash_token(new_refresh_data["refresh_token"])

        await self.session_repo.update_session_token(
            session_id=session.id,
            new_token_hash=new_hash,
            new_expires_at=new_refresh_data["expires_at"]
        )

        new_access_data = create_access_token(user_id=str(user.id), role=user.role)

        await self.audit_service.log_event(
            action="TOKEN_REFRESH",
            user_id=user.id,
            details="Refresh token rotated successfully."
        )

        await self.db.commit()

        return {
            "access_token": new_access_data["access_token"],
            "refresh_token": new_refresh_data["refresh_token"],
            "token_type": "bearer"
        }

    async def logout(self, refresh_token: Optional[str] = None, access_token: Optional[str] = None) -> bool:
        if refresh_token:
            try:
                payload = decode_refresh_token(refresh_token)
                session_id_str = payload.get("session_id")
                if session_id_str:
                    await self.session_repo.revoke_session(uuid.UUID(session_id_str))
            except Exception:
                pass

        if access_token:
            try:
                payload = decode_access_token(access_token)
                jti = payload.get("jti")
                exp = payload.get("exp")
                user_id_str = payload.get("sub")
                if jti and exp:
                    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                    user_id = uuid.UUID(user_id_str) if user_id_str else None
                    await self.token_repo.blacklist_token(
                        jti=jti,
                        token_type="access",
                        user_id=user_id,
                        expires_at=expires_at
                    )
            except Exception:
                pass

        await self.db.commit()
        return True

    async def logout_all(self, user_id: uuid.UUID) -> bool:
        await self.session_repo.revoke_all_user_sessions(user_id)
        await self.audit_service.log_event(
            action="LOGOUT_ALL_DEVICES",
            user_id=user_id,
            details="Logged out of all devices and active sessions."
        )
        await self.db.commit()
        return True

    async def forgot_password(self, email: str) -> str:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return "If the email is registered, a password reset token has been generated."

        reset_token = generate_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        user.reset_password_token = reset_token
        user.reset_password_expires_at = expires_at

        await self.audit_service.log_event(
            action="FORGOT_PASSWORD_REQUESTED",
            user_id=user.id,
            details=f"Password reset token generated for {user.email}"
        )
        await self.db.commit()

        # Send HTML password reset email
        await EmailService.send_password_reset_email(
            to_email=user.email,
            first_name=user.first_name,
            reset_token=reset_token
        )

        return reset_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        user = await self.user_repo.get_by_reset_token(token)
        if not user:
            raise ValidationError("Invalid or expired password reset token")

        if user.reset_password_expires_at:
            expires_at = user.reset_password_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise ValidationError("Password reset token has expired")

        user.hashed_password = hash_password(new_password)
        user.reset_password_token = None
        user.reset_password_expires_at = None

        await self.session_repo.revoke_all_user_sessions(user.id)

        await self.audit_service.log_event(
            action="PASSWORD_RESET_SUCCESS",
            user_id=user.id,
            details=f"Password reset successfully for {user.email}. All existing sessions revoked."
        )
        await self.db.commit()
        return True
