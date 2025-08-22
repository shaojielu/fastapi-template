from fastapi.testclient import TestClient

import pytest
from app.core.config import settings
from app.models import User

def def_url(uri:str):
    return f"{settings.API_V1_STR}{uri}"

pytestmark = pytest.mark.asyncio

async def test_login_access_token(client: TestClient, existing_user: User):
    """
    Test successful login and access token generation.
    """
    login_data = {
        "username": existing_user.email,
        "password": "a-plain-password",  # The plain password from conftest
    }
    response = client.post(def_url("/login/access-token"), data=login_data)
    response_json = response.json()
    assert response.status_code == 200
    assert "access_token" in response_json
    assert response_json["token_type"] == "bearer"

async def test_login_incorrect_password(client: TestClient, existing_user: User):
    """
    Test login with an incorrect password.
    """
    login_data = {
        "username": existing_user.email,
        "password": "wrong-password",
    }
    response = client.post(def_url("/login/access-token"), data=login_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

async def test_login_nonexistent_user(client: TestClient):
    """
    Test login with a nonexistent user.
    """
    login_data = {
        "username": "nonexistent@example.com",
        "password": "any-password",
    }
    response = client.post(def_url("/login/access-token"), data=login_data)
    # 将 400 改为 401
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
