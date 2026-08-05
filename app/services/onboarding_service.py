import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.onboarding_repository import OnboardingRepository
from app.services.audit_service import AuditService
from app.core.exceptions import ConflictError, ValidationError

ONBOARDING_STEPS: List[str] = [
    "company",
    "address",
    "logo",
    "departments",
    "job-titles",
    "work-locations",
    "shifts",
    "leave-policy",
    "payroll",
    "holidays",
    "invite",
    "finish"
]


class OnboardingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.onboarding_repo = OnboardingRepository(db)
        self.audit_service = AuditService(db)

    def get_status(self, user: User) -> Dict[str, Any]:
        if user.onboarding_completed:
            return {
                "current_step": "finish",
                "completed_steps": ONBOARDING_STEPS,
                "remaining_steps": [],
                "onboarding_completed": True
            }

        curr_step = user.onboarding_step if user.onboarding_step in ONBOARDING_STEPS else "company"
        idx = ONBOARDING_STEPS.index(curr_step)

        completed_steps = ONBOARDING_STEPS[:idx]
        current_step = ONBOARDING_STEPS[idx]
        remaining_steps = ONBOARDING_STEPS[idx + 1:]

        return {
            "current_step": current_step,
            "completed_steps": completed_steps,
            "remaining_steps": remaining_steps,
            "onboarding_completed": False
        }

    def _validate_step_access(self, user: User, target_step: str):
        if user.onboarding_completed:
            raise ConflictError("Onboarding has already been completed. All steps are locked.")

        status = self.get_status(user)
        if target_step in status["completed_steps"]:
            raise ConflictError(f"Step '{target_step}' is already completed and locked. Modifications are not allowed.")

        if target_step != status["current_step"]:
            raise ValidationError(
                f"Cannot access step '{target_step}'. Current pending step is '{status['current_step']}'."
            )

    async def _advance_step(self, user: User, current_step: str) -> str:
        idx = ONBOARDING_STEPS.index(current_step)
        if idx + 1 < len(ONBOARDING_STEPS):
            next_step = ONBOARDING_STEPS[idx + 1]
            await self.user_repo.update_onboarding_step(user.id, next_step=next_step, completed=False)
            user.onboarding_step = next_step
            await self.db.commit()
            return next_step
        else:
            await self.user_repo.update_onboarding_step(user.id, next_step="finish", completed=True)
            user.onboarding_completed = True
            user.onboarding_step = "finish"
            await self.db.commit()
            return "finish"

    async def submit_company(self, user: User, data: dict) -> Dict[str, Any]:
        self._validate_step_access(user, "company")
        result = await self.onboarding_repo.save_company_profile(user.id, data)
        next_step = await self._advance_step(user, "company")
        await self.audit_service.log_event("ONBOARDING_COMPANY_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_address(self, user: User, data: dict) -> Dict[str, Any]:
        self._validate_step_access(user, "address")
        result = await self.onboarding_repo.save_company_address(user.id, data)
        next_step = await self._advance_step(user, "address")
        await self.audit_service.log_event("ONBOARDING_ADDRESS_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_logo(self, user: User, data: dict) -> Dict[str, Any]:
        self._validate_step_access(user, "logo")
        result = await self.onboarding_repo.save_company_logo(user.id, data)
        next_step = await self._advance_step(user, "logo")
        await self.audit_service.log_event("ONBOARDING_LOGO_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_departments(self, user: User, data: list) -> Dict[str, Any]:
        self._validate_step_access(user, "departments")
        result = await self.onboarding_repo.save_departments(user.id, data)
        next_step = await self._advance_step(user, "departments")
        await self.audit_service.log_event("ONBOARDING_DEPARTMENTS_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_job_titles(self, user: User, data: list) -> Dict[str, Any]:
        self._validate_step_access(user, "job-titles")
        result = await self.onboarding_repo.save_job_titles(user.id, data)
        next_step = await self._advance_step(user, "job-titles")
        await self.audit_service.log_event("ONBOARDING_JOB_TITLES_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_work_locations(self, user: User, data: list) -> Dict[str, Any]:
        self._validate_step_access(user, "work-locations")
        result = await self.onboarding_repo.save_work_locations(user.id, data)
        next_step = await self._advance_step(user, "work-locations")
        await self.audit_service.log_event("ONBOARDING_WORK_LOCATIONS_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_shifts(self, user: User, data: list) -> Dict[str, Any]:
        self._validate_step_access(user, "shifts")
        result = await self.onboarding_repo.save_shifts(user.id, data)
        next_step = await self._advance_step(user, "shifts")
        await self.audit_service.log_event("ONBOARDING_SHIFTS_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_leave_policy(self, user: User, data: dict) -> Dict[str, Any]:
        self._validate_step_access(user, "leave-policy")
        result = await self.onboarding_repo.save_leave_policy(user.id, data)
        next_step = await self._advance_step(user, "leave-policy")
        await self.audit_service.log_event("ONBOARDING_LEAVE_POLICY_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_payroll(self, user: User, data: dict) -> Dict[str, Any]:
        self._validate_step_access(user, "payroll")
        result = await self.onboarding_repo.save_payroll(user.id, data)
        next_step = await self._advance_step(user, "payroll")
        await self.audit_service.log_event("ONBOARDING_PAYROLL_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_holidays(self, user: User, data: list) -> Dict[str, Any]:
        self._validate_step_access(user, "holidays")
        result = await self.onboarding_repo.save_holidays(user.id, data)
        next_step = await self._advance_step(user, "holidays")
        await self.audit_service.log_event("ONBOARDING_HOLIDAYS_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def submit_invite(self, user: User, data: list) -> Dict[str, Any]:
        self._validate_step_access(user, "invite")
        result = await self.onboarding_repo.save_invitations(user.id, data)
        next_step = await self._advance_step(user, "invite")
        await self.audit_service.log_event("ONBOARDING_INVITE_SUBMITTED", user_id=user.id)
        await self.db.commit()
        return {"data": result, "next_step": next_step}

    async def finish_onboarding(self, user: User) -> Dict[str, Any]:
        self._validate_step_access(user, "finish")
        await self.user_repo.update_onboarding_step(user.id, next_step="finish", completed=True)
        user.onboarding_completed = True
        user.onboarding_step = "finish"
        await self.audit_service.log_event("ONBOARDING_COMPLETED", user_id=user.id)
        await self.db.commit()
        return {
            "onboarding_completed": True,
            "next_step": "/dashboard"
        }
