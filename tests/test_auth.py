import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, lifespan


@pytest.fixture
async def client():
    async with lifespan(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c


@pytest.mark.asyncio
async def test_register_login_me(client):
    creds = {"email": "a@example.com", "password": "supersecret1"}
    r = await client.post("/auth/register", json=creds)
    assert r.status_code == 201

    r = await client.post(
        "/auth/login", data={"username": creds["email"], "password": creds["password"]}
    )
    assert r.status_code == 200
    tokens = r.json()

    r = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == creds["email"]

    r = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
