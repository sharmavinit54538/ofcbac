import pytest
from httpx import AsyncClient

USER_PAYLOAD = {
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice.smith@example.com",
    "password": "Password123!",
    "confirm_password": "Password123!",
    "company_name": "Tech Corp",
    "role": "Organization Admin"
}


@pytest.mark.asyncio
async def test_full_onboarding_flow_and_step_locking(client: AsyncClient):
    # Register & verify
    reg_res = await client.post("/auth/register", json=USER_PAYLOAD)
    otp = reg_res.json()["data"]["otp_debug"]
    await client.post("/auth/verify-email", json={"email": USER_PAYLOAD["email"], "otp": otp})

    login_res = await client.post("/auth/login", json={"email": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]})
    access_token = login_res.json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # GET /onboarding/status
    status_res = await client.get("/onboarding/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["current_step"] == "company"

    # Step 1: /onboarding/company
    company_payload = {
        "company_name": "Tech Corp",
        "industry": "Software",
        "company_size": "50-100",
        "website": "https://techcorp.com"
    }
    step1_res = await client.post("/onboarding/company", json=company_payload, headers=headers)
    assert step1_res.status_code == 200
    assert step1_res.json()["data"]["next_step"] == "address"

    # STEP LOCKING CHECK: Try calling /onboarding/company again -> Expect 409 Conflict Error
    step1_retry = await client.post("/onboarding/company", json=company_payload, headers=headers)
    assert step1_retry.status_code == 409
    assert step1_retry.json()["success"] is False

    # Step 2: /onboarding/address
    address_payload = {
        "street_address": "123 Innovation Way",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94105",
        "country": "USA"
    }
    step2_res = await client.post("/onboarding/address", json=address_payload, headers=headers)
    assert step2_res.status_code == 200
    assert step2_res.json()["data"]["next_step"] == "logo"

    # Step 3: /onboarding/logo
    logo_payload = {"logo_url": "https://techcorp.com/logo.png", "file_name": "logo.png"}
    step3_res = await client.post("/onboarding/logo", json=logo_payload, headers=headers)
    assert step3_res.status_code == 200
    assert step3_res.json()["data"]["next_step"] == "departments"

    # Step 4: /onboarding/departments
    dept_payload = {"departments": [{"name": "Engineering", "code": "ENG"}, {"name": "HR", "code": "HR"}]}
    step4_res = await client.post("/onboarding/departments", json=dept_payload, headers=headers)
    assert step4_res.status_code == 200

    # Step 5: /onboarding/job-titles
    jobs_payload = {"job_titles": [{"title": "Senior Software Engineer", "department_name": "Engineering"}]}
    step5_res = await client.post("/onboarding/job-titles", json=jobs_payload, headers=headers)
    assert step5_res.status_code == 200

    # Step 6: /onboarding/work-locations
    locs_payload = {"locations": [{"name": "HQ San Francisco", "address": "123 Innovation Way", "timezone": "America/Los_Angeles"}]}
    step6_res = await client.post("/onboarding/work-locations", json=locs_payload, headers=headers)
    assert step6_res.status_code == 200

    # Step 7: /onboarding/shifts
    shifts_payload = {"shifts": [{"name": "Standard Morning", "start_time": "09:00", "end_time": "17:00", "work_days": "Mon-Fri"}]}
    step7_res = await client.post("/onboarding/shifts", json=shifts_payload, headers=headers)
    assert step7_res.status_code == 200

    # Step 8: /onboarding/leave-policy
    leave_payload = {"policy_name": "Standard Unlimited PTO", "annual_leave_days": 20, "sick_leave_days": 10, "carry_over_allowed": True}
    step8_res = await client.post("/onboarding/leave-policy", json=leave_payload, headers=headers)
    assert step8_res.status_code == 200

    # Step 9: /onboarding/payroll
    payroll_payload = {"currency": "USD", "pay_cycle": "Monthly", "pay_day": 28}
    step9_res = await client.post("/onboarding/payroll", json=payroll_payload, headers=headers)
    assert step9_res.status_code == 200

    # Step 10: /onboarding/holidays
    holidays_payload = {"holidays": [{"holiday_name": "New Year's Day", "date": "2026-01-01", "is_optional": False}]}
    step10_res = await client.post("/onboarding/holidays", json=holidays_payload, headers=headers)
    assert step10_res.status_code == 200

    # Step 11: /onboarding/invite
    invite_payload = {"invitations": [{"email": "bob.engineer@techcorp.com", "role": "Employee"}]}
    step11_res = await client.post("/onboarding/invite", json=invite_payload, headers=headers)
    assert step11_res.status_code == 200

    # Step 12: /onboarding/finish
    finish_res = await client.post("/onboarding/finish", json={"confirm_finish": True}, headers=headers)
    assert finish_res.status_code == 200
    assert finish_res.json()["data"]["onboarding_completed"] is True
    assert finish_res.json()["data"]["next_step"] == "/dashboard"

    # Subsequent login returns next_step == "/dashboard"
    login_after_finish = await client.post("/auth/login", json={"email": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]})
    assert login_after_finish.json()["data"]["onboarding_completed"] is True
    assert login_after_finish.json()["data"]["next_step"] == "/dashboard"
