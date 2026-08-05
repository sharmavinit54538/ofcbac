from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.response import success_response, error_response
from app.config.settings import settings
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, VerifyEmailRequest, ResendVerificationRequest, LoginRequest,
    RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest,
    GoogleOAuthRequest, OktaSSORequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=settings.COOKIE_DOMAIN,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        domain=settings.COOKIE_DOMAIN,
        path="/"
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie(key="access_token", domain=settings.COOKIE_DOMAIN, path="/")
    response.delete_cookie(key="refresh_token", domain=settings.COOKIE_DOMAIN, path="/")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    auth_service = AuthService(db)
    result = await auth_service.register(payload, ip_address=ip_address, user_agent=user_agent)

    _set_auth_cookies(
        response,
        access_token=result["tokens"]["access_token"],
        refresh_token=result["tokens"]["refresh_token"]
    )

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=result,
        message="User registered successfully. Verification email sent.",
        request_id=request_id
    )


@router.post("/verify-email")
async def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    auth_service = AuthService(db)
    await auth_service.verify_email(payload.email, payload.otp)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"email": payload.email, "is_verified": True},
        message="Email verified successfully.",
        request_id=request_id
    )


@router.post("/resend-verification")
@router.post("/verify-email/resend")
async def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    auth_service = AuthService(db)
    result = await auth_service.resend_verification_otp(payload.email)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=result,
        message=result["message"],
        request_id=request_id
    )


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    auth_service = AuthService(db)
    result = await auth_service.login(payload, ip_address=ip_address, user_agent=user_agent)

    _set_auth_cookies(
        response,
        access_token=result["tokens"]["access_token"],
        refresh_token=result["tokens"]["refresh_token"]
    )

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=result,
        message="Login successful.",
        request_id=request_id
    )


@router.post("/refresh")
async def refresh_tokens(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_async_db)
):
    refresh_token = None
    if payload and payload.refresh_token:
        refresh_token = payload.refresh_token
    else:
        refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return error_response("Refresh token missing from request payload or cookie", request_id=getattr(request.state, "request_id", None))

    auth_service = AuthService(db)
    new_tokens = await auth_service.refresh_tokens(refresh_token)

    _set_auth_cookies(
        response,
        access_token=new_tokens["access_token"],
        refresh_token=new_tokens["refresh_token"]
    )

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=new_tokens,
        message="Tokens refreshed successfully.",
        request_id=request_id
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_async_db)
):
    refresh_token = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    access_token = request.cookies.get("access_token")
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]

    auth_service = AuthService(db)
    await auth_service.logout(refresh_token=refresh_token, access_token=access_token)

    _clear_auth_cookies(response)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=None,
        message="Logged out successfully.",
        request_id=request_id
    )


@router.post("/logout-all")
async def logout_all(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    auth_service = AuthService(db)
    await auth_service.logout_all(current_user.id)

    _clear_auth_cookies(response)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=None,
        message="Logged out of all active devices and sessions.",
        request_id=request_id
    )


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    auth_service = AuthService(db)
    reset_token = await auth_service.forgot_password(payload.email)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"email": payload.email, "reset_token_debug": reset_token},
        message="Password reset instructions sent if email exists.",
        request_id=request_id
    )


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    auth_service = AuthService(db)
    await auth_service.reset_password(payload.token, payload.new_password)

    _clear_auth_cookies(response)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=None,
        message="Password reset successfully. Please log in with your new password.",
        request_id=request_id
    )


@router.post("/google")
async def google_login(
    payload: GoogleOAuthRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    oauth_service = OAuthService(db)
    result = await oauth_service.google_login(
        credential=payload.credential,
        ip_address=ip_address,
        user_agent=user_agent
    )

    _set_auth_cookies(
        response,
        access_token=result["tokens"]["access_token"],
        refresh_token=result["tokens"]["refresh_token"]
    )

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=result,
        message="Google OAuth login successful.",
        request_id=request_id
    )


@router.post("/okta")
async def okta_login(
    payload: OktaSSORequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    oauth_service = OAuthService(db)
    result = await oauth_service.okta_login(
        code=payload.code,
        redirect_uri=payload.redirect_uri,
        ip_address=ip_address,
        user_agent=user_agent
    )

    _set_auth_cookies(
        response,
        access_token=result["tokens"]["access_token"],
        refresh_token=result["tokens"]["refresh_token"]
    )

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=result,
        message="Okta SSO login successful.",
        request_id=request_id
    )
