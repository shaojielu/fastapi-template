from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.models import User

def def_url(uri:str):
    return f"{settings.API_V1_STR}{uri}"

pytestmark = pytest.mark.asyncio

async def test_create_user(client: TestClient):
    """
    Test creating a new user.
    """
    user_data = {
        "full_name": "New Test User",
        "email": "newuser@example.com",
        "password": "newpassword123",
    }
    response = client.post(def_url("/users/"), json=user_data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert "id" in created_user
    assert "hashed_password" not in created_user

async def test_create_user_existing_email(client: TestClient, existing_user: User):
    """
    Test creating a user with an already existing email.
    """
    user_data = {
        "full_name": "Another User",
        "email": existing_user.email,  # Use existing user's email
        "password": "anypassword",
    }
    response = client.post(def_url("/users/"), json=user_data)
    assert response.status_code == 400
    # 修改期望的错误信息
    assert "Email already registered" in response.json()["detail"]

async def test_read_user_me(client: TestClient, auth_headers: dict[str, str]):
    """
    Test fetching the current user's data.
    """
    response = client.get(def_url("/users/me"), headers=auth_headers)
    assert response.status_code == 200
    user = response.json()
    assert "email" in user
    assert "full_name" in user

async def test_update_user(client: TestClient, existing_user: User, auth_headers: dict[str, str]):
    """
    Test updating the current user's information.
    """
    update_data = {"full_name": "Updated Name"}
    response = client.put(
        def_url(f"/users/{existing_user.id}"),
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["full_name"] == "Updated Name"
    assert updated_user["email"] == existing_user.email

async def test_update_other_user_not_allowed(client: TestClient, another_user: User, auth_headers: dict[str, str]):
    """
    Test that a user cannot update another user's information.
    """
    update_data = {"full_name": "Unauthorized Update"}
    response = client.put(
        def_url(f"/users/{another_user.id}"),
        json=update_data,
        headers=auth_headers, # Authenticated as `test_user`
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this user"
