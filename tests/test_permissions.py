import pytest
from httpx import AsyncClient
from sqlalchemy import update
from app.models.user import User
from app.repositories.user_repository import UserRepository

EMP_PAYLOAD = {
    "first_name": "Bob",
    "last_name": "Worker",
    "email": "bob.worker@example.com",
    "password": "Password123!",
    "confirm_password": "Password123!",
    "company_name": "Acme Inc"
}


@pytest.mark.asyncio
async def test_rbac_permission_enforcement(client: AsyncClient, db_session):
    reg_res = await client.post("/auth/register", json=EMP_PAYLOAD)
    otp = reg_res.json()["data"]["otp_debug"]
    await client.post("/auth/verify-email", json={"email": EMP_PAYLOAD["email"], "otp": otp})

    # Demote user role to Employee in DB to test non-admin permission restriction
    await db_session.execute(
        update(User).where(User.email == EMP_PAYLOAD["email"]).values(role="Employee")
    )
    await db_session.commit()

    login_res = await client.post("/auth/login", json={"email": EMP_PAYLOAD["email"], "password": EMP_PAYLOAD["password"]})
    access_token = login_res.json()["data"]["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    admin_res = await client.get("/users/admin/users", headers=headers)
    assert admin_res.status_code == 403
    assert admin_res.json()["success"] is False
    assert "Access denied" in admin_res.json()["message"]
