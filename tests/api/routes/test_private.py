import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.schemas.users import PrivateUserCreate
from app.services.user import get_user_by_email
from tests.utils.utils import random_email, random_lower_string

pytestmark = pytest.mark.anyio


async def test_create_user(client: AsyncClient, db: AsyncSession) -> None:
    """测试通过私有 API 创建用户"""
    username = random_email()
    password = random_lower_string()
    full_name = "Test User"
    user_in = PrivateUserCreate(email=username, password=password, full_name=full_name)
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
    )
    assert 200 <= response.status_code < 300
    created_user = response.json()
    user = await get_user_by_email(db, username)
    assert user
    assert user.email == created_user["email"]
    assert user.full_name == full_name


async def test_create_user_verify_password(
    client: AsyncClient, db: AsyncSession
) -> None:
    """测试通过私有 API 创建的用户密码正确"""
    username = random_email()
    password = random_lower_string()
    full_name = "Test User Password"
    user_in = PrivateUserCreate(email=username, password=password, full_name=full_name)
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
    )
    assert response.status_code == 200

    user = await get_user_by_email(db, username)
    assert user
    assert verify_password(password, user.hashed_password)


async def test_create_user_default_values(
    client: AsyncClient, db: AsyncSession
) -> None:
    """测试通过私有 API 创建用户的默认值"""
    username = random_email()
    password = random_lower_string()
    full_name = "Default Values Test"
    user_in = PrivateUserCreate(email=username, password=password, full_name=full_name)
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
    )
    assert response.status_code == 200
    created_user = response.json()

    # 检查默认值
    assert created_user["is_active"] is True
    assert created_user["is_superuser"] is False


async def test_create_user_response_fields(
    client: AsyncClient, db: AsyncSession
) -> None:
    """测试私有 API 创建用户响应包含所有必要字段"""
    username = random_email()
    password = random_lower_string()
    full_name = "Response Fields Test"
    user_in = PrivateUserCreate(email=username, password=password, full_name=full_name)
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
    )
    assert response.status_code == 200
    created_user = response.json()

    # 检查响应包含所有必要字段
    assert "id" in created_user
    assert "email" in created_user
    assert "full_name" in created_user
    assert "is_active" in created_user
    assert "is_superuser" in created_user
    # 确保不返回密码
    assert "password" not in created_user
    assert "hashed_password" not in created_user


async def test_create_user_can_login(client: AsyncClient, db: AsyncSession) -> None:
    """测试通过私有 API 创建的用户可以登录"""
    username = random_email()
    password = random_lower_string()
    full_name = "Login Test User"
    user_in = PrivateUserCreate(email=username, password=password, full_name=full_name)

    # 创建用户
    response = await client.post(
        f"{settings.API_V1_STR}/private/users/",
        json=user_in.model_dump(),
    )
    assert response.status_code == 200

    # 尝试登录
    login_data = {"username": username, "password": password}
    login_response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data,
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert tokens["access_token"]


async def test_create_multiple_users(client: AsyncClient, db: AsyncSession) -> None:
    """测试创建多个用户"""
    users_data = []
    for i in range(3):
        user_in = PrivateUserCreate(
            email=random_email(),
            password=random_lower_string(),
            full_name=f"Test User {i}",
        )
        users_data.append(user_in)

    for user_in in users_data:
        response = await client.post(
            f"{settings.API_V1_STR}/private/users/",
            json=user_in.model_dump(),
        )
        assert response.status_code == 200

    # 验证所有用户都被创建
    for user_in in users_data:
        user = await get_user_by_email(db, user_in.email)
        assert user is not None
        assert user.email == user_in.email
