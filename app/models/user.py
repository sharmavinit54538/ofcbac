from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="Organization Admin", nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_step: Mapped[str] = mapped_column(String(50), default="company", nullable=False)
    
    verification_otp: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    verification_otp_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    reset_password_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_password_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
