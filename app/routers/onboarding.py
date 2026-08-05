from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.response import success_response
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.onboarding_service import OnboardingService
from app.schemas.onboarding import (
    CompanyProfileSchema, CompanyAddressSchema, CompanyLogoSchema,
    DepartmentsSchema, JobTitlesSchema, WorkLocationsSchema,
    ShiftsSchema, LeavePolicySchema, PayrollSchema, HolidaysSchema,
    InviteSchema, FinishSchema
)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/status")
async def get_onboarding_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    status_info = service.get_status(current_user)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=status_info,
        message="Onboarding status retrieved successfully.",
        request_id=request_id
    )


@router.post("/company")
async def submit_company(
    payload: CompanyProfileSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    res = await service.submit_company(current_user, payload.model_dump())

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Company profile saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/address")
async def submit_address(
    payload: CompanyAddressSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    res = await service.submit_address(current_user, payload.model_dump())

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Company address saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/logo")
async def submit_logo(
    payload: CompanyLogoSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    res = await service.submit_logo(current_user, payload.model_dump())

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Company logo saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/departments")
async def submit_departments(
    payload: DepartmentsSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    deps_data = [item.model_dump() for item in payload.departments]
    res = await service.submit_departments(current_user, deps_data)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Departments saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/job-titles")
async def submit_job_titles(
    payload: JobTitlesSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    titles_data = [item.model_dump() for item in payload.job_titles]
    res = await service.submit_job_titles(current_user, titles_data)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Job titles saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/work-locations")
async def submit_work_locations(
    payload: WorkLocationsSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    locs_data = [item.model_dump() for item in payload.locations]
    res = await service.submit_work_locations(current_user, locs_data)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Work locations saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/shifts")
async def submit_shifts(
    payload: ShiftsSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    shifts_data = [item.model_dump() for item in payload.shifts]
    res = await service.submit_shifts(current_user, shifts_data)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Shift configuration saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/leave-policy")
async def submit_leave_policy(
    payload: LeavePolicySchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    res = await service.submit_leave_policy(current_user, payload.model_dump())

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Leave policy saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/payroll")
async def submit_payroll(
    payload: PayrollSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    res = await service.submit_payroll(current_user, payload.model_dump())

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Payroll settings saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/holidays")
async def submit_holidays(
    payload: HolidaysSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    hols_data = [item.model_dump() for item in payload.holidays]
    res = await service.submit_holidays(current_user, hols_data)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Holiday calendar saved successfully. Step locked.",
        request_id=request_id
    )


@router.post("/invite")
async def submit_invite(
    payload: InviteSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    invs_data = [item.model_dump() for item in payload.invitations]
    res = await service.submit_invite(current_user, invs_data)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Employee invitations sent successfully. Step locked.",
        request_id=request_id
    )


@router.post("/finish")
async def finish_onboarding(
    payload: FinishSchema,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    service = OnboardingService(db)
    res = await service.finish_onboarding(current_user)

    request_id = getattr(request.state, "request_id", None)
    return success_response(
        data=res,
        message="Onboarding completed successfully. Welcome to OFC HR Dashboard!",
        request_id=request_id
    )
