from typing import List
from fastapi import Depends
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.core.exceptions import PermissionDeniedError


class RequireRole:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles and current_user.role != "Super Admin":
            raise PermissionDeniedError(
                f"Access denied. Requires one of roles: {', '.join(self.allowed_roles)}"
            )
        return current_user


class RequirePermission:
    def __init__(self, permission_code: str):
        self.permission_code = permission_code

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        # Super Admin and Organization Admin have full access
        if current_user.role in ["Super Admin", "Organization Admin"]:
            return current_user
        
        # Check granular permissions attached to role if extended
        raise PermissionDeniedError(f"Permission '{self.permission_code}' denied for user role '{current_user.role}'")
