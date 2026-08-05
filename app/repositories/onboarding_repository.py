import uuid
from typing import List, Optional, Type, TypeVar
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.onboarding import (
    CompanyProfile, CompanyAddress, CompanyLogo, Department,
    JobTitle, WorkLocation, ShiftConfig, LeavePolicy,
    PayrollSetting, HolidayCalendar, EmployeeInvitation
)

T = TypeVar("T")


class OnboardingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_company_profile(self, user_id: uuid.UUID, data: dict) -> CompanyProfile:
        stmt = select(CompanyProfile).where(CompanyProfile.user_id == user_id)
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            profile = existing
        else:
            profile = CompanyProfile(user_id=user_id, **data)
            self.db.add(profile)
        await self.db.flush()
        return profile

    async def save_company_address(self, user_id: uuid.UUID, data: dict) -> CompanyAddress:
        stmt = select(CompanyAddress).where(CompanyAddress.user_id == user_id)
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            address = existing
        else:
            address = CompanyAddress(user_id=user_id, **data)
            self.db.add(address)
        await self.db.flush()
        return address

    async def save_company_logo(self, user_id: uuid.UUID, data: dict) -> CompanyLogo:
        stmt = select(CompanyLogo).where(CompanyLogo.user_id == user_id)
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            logo = existing
        else:
            logo = CompanyLogo(user_id=user_id, **data)
            self.db.add(logo)
        await self.db.flush()
        return logo

    async def save_departments(self, user_id: uuid.UUID, departments_data: list) -> List[Department]:
        await self.db.execute(delete(Department).where(Department.user_id == user_id))
        deps = [Department(user_id=user_id, **d) for d in departments_data]
        self.db.add_all(deps)
        await self.db.flush()
        return deps

    async def save_job_titles(self, user_id: uuid.UUID, titles_data: list) -> List[JobTitle]:
        await self.db.execute(delete(JobTitle).where(JobTitle.user_id == user_id))
        titles = [JobTitle(user_id=user_id, **t) for t in titles_data]
        self.db.add_all(titles)
        await self.db.flush()
        return titles

    async def save_work_locations(self, user_id: uuid.UUID, locations_data: list) -> List[WorkLocation]:
        await self.db.execute(delete(WorkLocation).where(WorkLocation.user_id == user_id))
        locs = [WorkLocation(user_id=user_id, **l) for l in locations_data]
        self.db.add_all(locs)
        await self.db.flush()
        return locs

    async def save_shifts(self, user_id: uuid.UUID, shifts_data: list) -> List[ShiftConfig]:
        await self.db.execute(delete(ShiftConfig).where(ShiftConfig.user_id == user_id))
        shifts = [ShiftConfig(user_id=user_id, **s) for s in shifts_data]
        self.db.add_all(shifts)
        await self.db.flush()
        return shifts

    async def save_leave_policy(self, user_id: uuid.UUID, data: dict) -> LeavePolicy:
        stmt = select(LeavePolicy).where(LeavePolicy.user_id == user_id)
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            policy = existing
        else:
            policy = LeavePolicy(user_id=user_id, **data)
            self.db.add(policy)
        await self.db.flush()
        return policy

    async def save_payroll(self, user_id: uuid.UUID, data: dict) -> PayrollSetting:
        stmt = select(PayrollSetting).where(PayrollSetting.user_id == user_id)
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            payroll = existing
        else:
            payroll = PayrollSetting(user_id=user_id, **data)
            self.db.add(payroll)
        await self.db.flush()
        return payroll

    async def save_holidays(self, user_id: uuid.UUID, holidays_data: list) -> List[HolidayCalendar]:
        await self.db.execute(delete(HolidayCalendar).where(HolidayCalendar.user_id == user_id))
        hols = [HolidayCalendar(user_id=user_id, **h) for h in holidays_data]
        self.db.add_all(hols)
        await self.db.flush()
        return hols

    async def save_invitations(self, user_id: uuid.UUID, invitations_data: list) -> List[EmployeeInvitation]:
        await self.db.execute(delete(EmployeeInvitation).where(EmployeeInvitation.user_id == user_id))
        invs = [EmployeeInvitation(user_id=user_id, **i) for i in invitations_data]
        self.db.add_all(invs)
        await self.db.flush()
        return invs
