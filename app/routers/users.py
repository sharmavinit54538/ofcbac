from fastapi import APIRouter, Depends, Request
from app.core.response import success_response
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import RequireRole
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=UserResponse.model_validate(current_user),
        message="User profile retrieved successfully.",
        request_id=request_id
    )


@router.get("/dashboard")
async def get_user_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={
            "user_id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
            "company_name": current_user.company_name,
            "onboarding_completed": current_user.onboarding_completed,
            "message": "Welcome to OFC HR Enterprise Dashboard"
        },
        message="Dashboard data retrieved.",
        request_id=request_id
    )


@router.get("/admin/users", dependencies=[Depends(RequireRole(["Super Admin", "Organization Admin"]))])
async def list_organization_users(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data={"users": [UserResponse.model_validate(current_user)]},
        message="Organization users listed successfully.",
        request_id=request_id
    )
