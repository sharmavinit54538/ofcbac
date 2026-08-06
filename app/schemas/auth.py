import re
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: EmailStr
    password: str
    confirm_password: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    organization_name: Optional[str] = None
    role: str = "Organization Admin"

    @model_validator(mode="before")
    @classmethod
    def normalize_registration_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize full_name / name to first_name and last_name
            full_name = data.get("full_name") or data.get("name")
            if full_name and not data.get("first_name"):
                parts = str(full_name).strip().split(" ", 1)
                data["first_name"] = parts[0]
                data["last_name"] = parts[1] if len(parts) > 1 else "."

            # Normalize organization_name / company / company_name
            org = (
                data.get("organization_name")
                or data.get("company_name")
                or data.get("company")
                or data.get("organization")
            )
            if org:
                data["company_name"] = str(org).strip()
                data["organization_name"] = str(org).strip()

            # Normalize confirm_password if missing
            if not data.get("confirm_password") and data.get("password"):
                data["confirm_password"] = data["password"]

            # Set robust defaults if any field is missing
            if not data.get("first_name"):
                data["first_name"] = "Admin"
            if not data.get("last_name"):
                data["last_name"] = "User"
            if not data.get("company_name"):
                data["company_name"] = "OFC HR Organization"

            data["role"] = "Organization Admin"

        return data

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: AuthTokenData
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    is_verified: bool
    onboarding_completed: bool
    next_step: str


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class GoogleOAuthRequest(BaseModel):
    id_token: Optional[str] = None
    credential: Optional[str] = None
    token: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_token(cls, data: Any) -> Any:
        if isinstance(data, dict):
            token_val = data.get("credential") or data.get("id_token") or data.get("token")
            if token_val:
                data["id_token"] = str(token_val)
        return data


class OktaSSORequest(BaseModel):
    code: str
    redirect_uri: str
