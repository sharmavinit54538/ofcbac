from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class OnboardingStatusResponse(BaseModel):
    current_step: str
    completed_steps: List[str]
    remaining_steps: List[str]
    onboarding_completed: bool


class CompanyProfileSchema(BaseModel):
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None


class CompanyAddressSchema(BaseModel):
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str


class CompanyLogoSchema(BaseModel):
    logo_url: str
    file_name: Optional[str] = None


class DepartmentItem(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None


class DepartmentsSchema(BaseModel):
    departments: List[DepartmentItem]


class JobTitleItem(BaseModel):
    title: str
    department_name: Optional[str] = None
    level: Optional[str] = None


class JobTitlesSchema(BaseModel):
    job_titles: List[JobTitleItem]


class LocationItem(BaseModel):
    name: str
    address: Optional[str] = None
    timezone: str = "UTC"


class WorkLocationsSchema(BaseModel):
    locations: List[LocationItem]


class ShiftItem(BaseModel):
    name: str
    start_time: str
    end_time: str
    work_days: str = "Mon-Fri"


class ShiftsSchema(BaseModel):
    shifts: List[ShiftItem]


class LeavePolicySchema(BaseModel):
    policy_name: str
    annual_leave_days: int = 15
    sick_leave_days: int = 10
    carry_over_allowed: bool = False


class PayrollSchema(BaseModel):
    currency: str = "USD"
    pay_cycle: str = "Monthly"
    pay_day: int = 28


class HolidayItem(BaseModel):
    holiday_name: str
    date: date
    is_optional: bool = False


class HolidaysSchema(BaseModel):
    holidays: List[HolidayItem]


class InvitationItem(BaseModel):
    email: EmailStr
    role: str = "Employee"


class InviteSchema(BaseModel):
    invitations: List[InvitationItem]


class FinishSchema(BaseModel):
    confirm_finish: bool = True
