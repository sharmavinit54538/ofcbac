import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_and_security_headers(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Request-ID" in res.headers
