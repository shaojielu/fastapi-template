import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.anyio


async def test_health_check(client: AsyncClient) -> None:
    """测试健康检查端点"""
    response = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 200
    assert response.json() is True


async def test_health_check_no_auth_required(client: AsyncClient) -> None:
    """测试健康检查端点不需要认证"""
    # 不带任何认证头
    response = await client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert response.status_code == 200


async def test_test_email_requires_superuser(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    """测试发送测试邮件端点需要超级用户权限"""
    response = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges"


async def test_test_email_no_auth(client: AsyncClient) -> None:
    """测试发送测试邮件端点需要认证"""
    response = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "test@example.com"},
    )
    assert response.status_code == 401


async def test_test_email_invalid_email(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """测试发送测试邮件端点验证邮箱格式"""
    response = await client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "invalid-email"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 422  # Validation error
