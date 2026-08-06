import pytest
from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "password": "Password123!",
    "confirm_password": "Password123!",
    "phone": "+1234567890",
    "company_name": "Acme Corp",
    "role": "Organization Admin"
}


@pytest.mark.asyncio
async def test_register_and_verify_email(client: AsyncClient):
    # Step 1: Register
    res = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["is_verified"] is False
    assert body["data"]["onboarding_completed"] is False
    assert body["data"]["next_step"] == "/onboarding/status"
    assert "access_token" in body["data"]["tokens"]
    assert "refresh_token" in body["data"]["tokens"]

    otp = body["data"]["otp_debug"]

    # Step 2: Resend Verification OTP
    resend_res = await client.post(
        "/auth/resend-verification",
        json={"email": "john.doe@example.com"}
    )
    assert resend_res.status_code == 200
    new_otp = resend_res.json()["data"]["otp_debug"]
    assert new_otp is not None

    # Step 3: Verify Email with new OTP
    verify_res = await client.post(
        "/auth/verify-email",
        json={"email": "john.doe@example.com", "otp": new_otp}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["is_verified"] is True


@pytest.mark.asyncio
async def test_login_and_token_refresh(client: AsyncClient):
    # Register & verify
    reg_res = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    otp = reg_res.json()["data"]["otp_debug"]
    await client.post("/auth/verify-email", json={"email": REGISTER_PAYLOAD["email"], "otp": otp})

    # Step 3: Login
    login_res = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    assert login_res.status_code == 200
    login_data = login_res.json()["data"]
    assert login_data["is_verified"] is True
    refresh_token = login_data["tokens"]["refresh_token"]

    # Step 4: Refresh Token Rotation
    refresh_res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    refreshed_data = refresh_res.json()["data"]
    assert "access_token" in refreshed_data
    assert "refresh_token" in refreshed_data
    assert refreshed_data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_logout_and_logout_all(client: AsyncClient):
    reg_res = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    otp = reg_res.json()["data"]["otp_debug"]
    await client.post("/auth/verify-email", json={"email": REGISTER_PAYLOAD["email"], "otp": otp})

    login_res = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    tokens = login_res.json()["data"]["tokens"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # Step 5: Logout
    logout_res = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_res.status_code == 200

    # Step 6: Logout-All
    login_res_2 = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    access_token_2 = login_res_2.json()["data"]["tokens"]["access_token"]

    logout_all_res = await client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token_2}"}
    )
    assert logout_all_res.status_code == 200


@pytest.mark.asyncio
async def test_forgot_and_reset_password(client: AsyncClient):
    reg_res = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    otp = reg_res.json()["data"]["otp_debug"]
    await client.post("/auth/verify-email", json={"email": REGISTER_PAYLOAD["email"], "otp": otp})

    # Step 7: Forgot password
    forgot_res = await client.post("/auth/forgot-password", json={"email": REGISTER_PAYLOAD["email"]})
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["data"]["reset_token_debug"]

    # Step 8: Reset password
    new_pw = "NewSecurePassword456!"
    reset_res = await client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": new_pw, "confirm_password": new_pw}
    )
    assert reset_res.status_code == 200

    # Login with new password
    login_new = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": new_pw}
    )
    assert login_new.status_code == 200


@pytest.mark.asyncio
async def test_google_and_okta_login(client: AsyncClient):
    # Step 9: Google login
    google_res = await client.post("/auth/google", json={"credential": "google_test_token_12345"})
    assert google_res.status_code == 200
    assert "access_token" in google_res.json()["data"]["tokens"]

    # Step 10: Okta login
    okta_res = await client.post("/auth/okta", json={"code": "okta_code_abc123", "redirect_uri": "http://localhost:3000/callback"})
    assert okta_res.status_code == 200
    assert "access_token" in okta_res.json()["data"]["tokens"]


@pytest.mark.asyncio
async def test_invalid_and_malformed_tokens(client: AsyncClient):
    # Register & login user to get valid token
    reg_res = await client.post("/auth/register", json={**REGISTER_PAYLOAD, "email": "malformed.test@example.com"})
    otp = reg_res.json()["data"]["otp_debug"]
    await client.post("/auth/verify-email", json={"email": "malformed.test@example.com", "otp": otp})

    login_res = await client.post(
        "/auth/login",
        json={"email": "malformed.test@example.com", "password": REGISTER_PAYLOAD["password"]}
    )
    valid_token = login_res.json()["data"]["tokens"]["access_token"]
    client.cookies.clear()

    # Test 1: Bearer null -> 401
    res = await client.get("/users/me", headers={"Authorization": "Bearer null"})
    assert res.status_code == 401

    # Test 2: Bearer undefined -> 401
    res = await client.get("/users/me", headers={"Authorization": "Bearer undefined"})
    assert res.status_code == 401

    # Test 3: Double Bearer -> Should sanitize and return 200
    res = await client.get("/users/me", headers={"Authorization": f"Bearer Bearer {valid_token}"})
    assert res.status_code == 200

    # Test 4: Quoted Bearer -> Should sanitize and return 200
    res = await client.get("/users/me", headers={"Authorization": f'Bearer "{valid_token}"'})
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_missing_refresh_token_returns_401(client: AsyncClient):
    res = await client.post("/auth/refresh", json={})
    assert res.status_code == 401
    assert res.json()["success"] is False

