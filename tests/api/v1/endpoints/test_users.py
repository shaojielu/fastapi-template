# test_users.py

from httpx import AsyncClient  # 明确导入 AsyncClient
import pytest

from app.core.config import settings
from app.models import User


def def_url(uri: str):
    return f"{settings.API_V1_STR}{uri}"


pytestmark = pytest.mark.anyio


# 【修改】改为 async def
async def test_create_user(client: AsyncClient):
    """
    测试创建一个新用户。
    """
    user_data = {
        "full_name": "New Test User",
        "email": "newuser@example.com",
        "password": "newpassword123",
    }
    # 【修改】使用 await
    response = await client.post(def_url("/users/"), json=user_data)
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert "id" in created_user
    assert "hashed_password" not in created_user


# 【修改】改为 async def
async def test_create_user_existing_email(client: AsyncClient, existing_user: User):
    """
    测试使用已存在的邮箱创建用户。
    """
    user_data = {
        "full_name": "Another User",
        "email": existing_user.email,
        "password": "anypassword",
    }
    # 【修改】使用 await
    response = await client.post(def_url("/users/"), json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


# 【修改】改为 async def
async def test_read_user_me(client: AsyncClient, auth_headers: dict[str, str]):
    """
    测试获取当前用户的数据。
    """
    # 【修改】使用 await
    response = await client.get(def_url("/users/me"), headers=auth_headers)
    assert response.status_code == 200
    user = response.json()
    assert "email" in user
    assert "full_name" in user


# 【修改】改为 async def
async def test_update_user(
    client: AsyncClient, existing_user: User, auth_headers: dict[str, str]
):
    """
    测试更新当前用户的信息。
    """
    update_data = {"full_name": "Updated Name"}
    # 【修改】使用 await
    response = await client.put(
        def_url(f"/users/{existing_user.id}"),
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["full_name"] == "Updated Name"
    assert updated_user["email"] == existing_user.email


# 【修改】改为 async def
async def test_update_other_user_not_allowed(
    client: AsyncClient, another_user: User, auth_headers: dict[str, str]
):
    """
    测试一个用户不能更新另一个用户的信息。
    """
    update_data = {"full_name": "Unauthorized Update"}
    # 【修改】使用 await
    response = await client.put(
        def_url(f"/users/{another_user.id}"),
        json=update_data,
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this user"
