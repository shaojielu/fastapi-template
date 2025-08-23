# test_login.py

import pytest
from httpx import AsyncClient  # 明确导入 AsyncClient

from app.core.config import settings
from app.models import User


def def_url(uri: str):
    return f"{settings.API_V1_STR}{uri}"


pytestmark = pytest.mark.anyio


# 【修改】改为 async def，并更新 client 类型提示
async def test_login_access_token(client: AsyncClient, existing_user: User):
    """
    测试成功的登录和访问令牌生成。
    """
    login_data = {
        "username": existing_user.email,
        "password": "a-plain-password",
    }
    # 【修改】使用 await
    response = await client.post(def_url("/login/access-token"), data=login_data)
    response_json = response.json()
    assert response.status_code == 200
    assert "access_token" in response_json
    assert response_json["token_type"] == "bearer"


# 【修改】改为 async def，并更新 client 类型提示
async def test_login_incorrect_password(client: AsyncClient, existing_user: User):
    """
    测试使用不正确的密码登录。
    """
    login_data = {
        "username": existing_user.email,
        "password": "wrong-password",
    }
    # 【修改】使用 await
    response = await client.post(def_url("/login/access-token"), data=login_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


# 【修改】改为 async def，并更新 client 类型提示
async def test_login_nonexistent_user(client: AsyncClient):
    """
    测试使用不存在的用户登录。
    """
    login_data = {
        "username": "nonexistent@example.com",
        "password": "any-password",
    }
    # 【修改】使用 await
    response = await client.post(def_url("/login/access-token"), data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
