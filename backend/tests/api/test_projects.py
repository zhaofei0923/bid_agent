"""Project CRUD endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /v1/projects creates a project."""
    response = await client.post(
        "/v1/projects",
        json={"name": "Test Project", "description": "My first project"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /v1/projects returns paginated project list."""
    response = await client.get("/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """GET /v1/projects without auth returns 401/403."""
    response = await client.get("/v1/projects")
    assert response.status_code in (401, 403)
