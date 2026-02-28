"""Auth endpoint tests."""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """POST /v1/auth/register creates a user and returns tokens."""
    response = await client.post(
        "/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "strongpass123",
            "name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """POST /v1/auth/register with existing email returns 422."""
    response = await client.post(
        "/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpass123",
            "name": "Dup User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user: User):
    """POST /v1/auth/login returns tokens for valid credentials."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user: User):
    """POST /v1/auth/login with wrong password returns 401."""
    response = await client.post(
        "/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /v1/auth/me returns current user profile."""
    response = await client.get("/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
