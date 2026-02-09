import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.utils.utils import generate_password_reset_token

pytestmark = pytest.mark.anyio


async def test_get_access_token(client: AsyncClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


async def test_get_access_token_incorrect_password(client: AsyncClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 401


async def test_get_access_token_nonexistent_user(client: AsyncClient) -> None:
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password123",
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect username or password"


async def test_test_token(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """测试 test-token 端点"""
    r = await client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    result = r.json()
    assert "email" in result
    assert result["email"] == settings.FIRST_SUPERUSER


async def test_test_token_no_auth(client: AsyncClient) -> None:
    """测试未授权时 test-token 端点返回错误"""
    r = await client.post(f"{settings.API_V1_STR}/login/test-token")
    assert r.status_code == 401


async def test_recover_password(client: AsyncClient) -> None:
    """测试密码恢复端点（用户不存在也返回成功，防止用户枚举）"""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery/nonexistent@example.com"
    )
    # 无论用户是否存在，都返回 200，防止用户枚举攻击
    assert r.status_code == 200
    assert r.json()["message"] == "Password recovery email sent"


async def test_reset_password_invalid_token(client: AsyncClient) -> None:
    """测试使用无效 token 重置密码"""
    r = await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": "invalid_token", "new_password": "newpassword123"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid token"


async def test_reset_password_nonexistent_user(client: AsyncClient) -> None:
    """测试为不存在的用户重置密码"""
    # 生成一个有效格式的 token，但是对应的邮箱不存在
    token = generate_password_reset_token(email="nonexistent@example.com")
    r = await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert r.status_code == 404
    assert "does not exist" in r.json()["detail"]


async def test_reset_password_success(client: AsyncClient) -> None:
    """测试成功重置密码"""
    # 为超级用户生成 token
    token = generate_password_reset_token(email=settings.FIRST_SUPERUSER)
    r = await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password updated successfully"

    # 恢复原密码以不影响其他测试
    token = generate_password_reset_token(email=settings.FIRST_SUPERUSER)
    await client.post(
        f"{settings.API_V1_STR}/login/reset-password/",
        json={"token": token, "new_password": settings.FIRST_SUPERUSER_PASSWORD},
    )


async def test_recover_password_html_content(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """测试获取密码恢复 HTML 内容端点"""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery-html-content/{settings.FIRST_SUPERUSER}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    # 验证返回的是 HTML 内容
    assert "<!doctype html>" in r.text.lower() or "<html" in r.text.lower()


async def test_recover_password_html_content_nonexistent_user(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """测试获取不存在用户的密码恢复 HTML 内容"""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery-html-content/nonexistent@example.com",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


async def test_recover_password_html_content_no_superuser(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    """测试非超级用户无法访问密码恢复 HTML 内容端点"""
    r = await client.post(
        f"{settings.API_V1_STR}/login/password-recovery-html-content/{settings.FIRST_SUPERUSER}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
