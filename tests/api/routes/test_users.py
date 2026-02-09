import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User
from app.schemas.users import UserCreate
from app.services.user import create_user
from tests.utils.utils import random_email, random_lower_string

pytestmark = pytest.mark.anyio


async def create_test_user(db: AsyncSession, email: str, password: str) -> User:
    """辅助函数：创建测试用户"""
    user_in = UserCreate(email=email, password=password)
    user = await create_user(db, user_in)
    await db.commit()
    return user


async def test_get_users_superuser_me(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers
    )
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER


async def test_get_users_normal_user_me(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
    )
    current_user = r.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


async def test_create_user_new_email(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    username = random_email()
    password = random_lower_string()
    data = {"email": username, "password": password}
    r = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    created_user = r.json()
    result = await db.execute(select(User).where(User.email == username))
    user = result.scalars().first()
    assert user
    assert user.email == created_user["email"]


async def test_get_existing_user(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    username = random_email()
    password = random_lower_string()
    user = await create_test_user(db, email=username, password=password)
    r = await client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    api_user = r.json()
    assert api_user["email"] == username


async def test_get_existing_user_current_user(
    client: AsyncClient, db: AsyncSession
) -> None:
    username = random_email()
    password = random_lower_string()
    user = await create_test_user(db, email=username, password=password)

    login_data = {"username": username, "password": password}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = await client.get(f"{settings.API_V1_STR}/users/{user.id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == username


async def test_get_existing_user_permissions_error(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = await client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"


async def test_create_user_existing_username(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    username = random_email()
    password = random_lower_string()
    await create_test_user(db, email=username, password=password)
    data = {"email": username, "password": password}
    r = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    assert "id" not in r.json()


async def test_create_user_by_normal_user(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"email": random_email(), "password": random_lower_string()}
    r = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 403


async def test_retrieve_users(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    await create_test_user(db, email=random_email(), password=random_lower_string())
    await create_test_user(db, email=random_email(), password=random_lower_string())

    r = await client.get(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers
    )
    all_users = r.json()

    assert len(all_users["data"]) > 1
    assert "count" in all_users
    for item in all_users["data"]:
        assert "email" in item


async def test_update_user_me(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    full_name = "Updated Name"
    email = random_email()
    data = {"full_name": full_name, "email": email}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated_user = r.json()
    assert updated_user["email"] == email
    assert updated_user["full_name"] == full_name

    user_query = select(User).where(User.email == email)
    user_db = (await db.execute(user_query)).scalars().first()
    assert user_db
    assert user_db.email == email
    assert user_db.full_name == full_name


async def test_update_password_me(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    new_password = random_lower_string()
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": new_password,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Password updated successfully"

    user_query = select(User).where(User.email == settings.FIRST_SUPERUSER)
    user_db = (await db.execute(user_query)).scalars().first()
    assert user_db
    assert verify_password(new_password, user_db.hashed_password)

    # Revert password
    old_data = {
        "current_password": new_password,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=old_data,
    )
    await db.refresh(user_db)
    assert r.status_code == 200
    assert verify_password(settings.FIRST_SUPERUSER_PASSWORD, user_db.hashed_password)


async def test_update_password_me_incorrect_password(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"current_password": "wrongpassword", "new_password": random_lower_string()}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect password"


async def test_update_user_me_email_exists(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    user = await create_test_user(
        db, email=random_email(), password=random_lower_string()
    )
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"email": user.email},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


async def test_update_password_me_same_password_error(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "current_password": settings.FIRST_SUPERUSER_PASSWORD,
        "new_password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "New password cannot be the same as the current one"


async def test_register_user(client: AsyncClient, db: AsyncSession) -> None:
    username = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    data = {"email": username, "password": password, "full_name": full_name}
    r = await client.post(f"{settings.API_V1_STR}/users/signup", json=data)
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == username
    assert created_user["full_name"] == full_name

    user_query = select(User).where(User.email == username)
    user_db = (await db.execute(user_query)).scalars().first()
    assert user_db
    assert verify_password(password, user_db.hashed_password)


async def test_register_user_already_exists_error(client: AsyncClient) -> None:
    data = {
        "email": settings.FIRST_SUPERUSER,
        "password": random_lower_string(),
        "full_name": random_lower_string(),
    }
    r = await client.post(f"{settings.API_V1_STR}/users/signup", json=data)
    assert r.status_code == 400
    assert r.json()["detail"] == "The user with this email already exists in the system"


async def test_update_user(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    user = await create_test_user(
        db, email=random_email(), password=random_lower_string()
    )
    data = {"full_name": "Updated_full_name"}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated_full_name"


async def test_update_user_not_exists(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"full_name": "Updated_full_name"}
    r = await client.patch(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "The user with this id does not exist in the system"


async def test_update_user_email_exists(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    user1 = await create_test_user(
        db, email=random_email(), password=random_lower_string()
    )
    user2 = await create_test_user(
        db, email=random_email(), password=random_lower_string()
    )

    r = await client.patch(
        f"{settings.API_V1_STR}/users/{user1.id}",
        headers=superuser_token_headers,
        json={"email": user2.email},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "User with this email already exists"


async def test_delete_user_me(client: AsyncClient, db: AsyncSession) -> None:
    username = random_email()
    password = random_lower_string()
    user = await create_test_user(db, email=username, password=password)
    user_id = user.id

    login_data = {"username": username, "password": password}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = await client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted successfully"

    result = await db.execute(select(User).where(User.id == user_id))
    assert result.scalars().first() is None


async def test_delete_user_me_as_superuser(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    r = await client.delete(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Super users are not allowed to delete themselves"


async def test_delete_user_super_user(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    user = await create_test_user(
        db, email=random_email(), password=random_lower_string()
    )
    user_id = user.id
    r = await client.delete(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted successfully"

    result = await db.execute(select(User).where(User.id == user_id))
    assert result.scalars().first() is None


async def test_delete_user_not_found(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    r = await client.delete(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


async def test_delete_user_current_super_user_error(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    super_user = await db.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    )
    super_user = super_user.scalars().first()
    assert super_user

    r = await client.delete(
        f"{settings.API_V1_STR}/users/{super_user.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Super users are not allowed to delete themselves"


async def test_delete_user_without_privileges(
    client: AsyncClient, normal_user_token_headers: dict[str, str], db: AsyncSession
) -> None:
    user = await create_test_user(
        db, email=random_email(), password=random_lower_string()
    )
    r = await client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"


async def test_get_users_pagination(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    """测试用户列表分页"""
    # 创建多个用户
    for _ in range(5):
        await create_test_user(db, email=random_email(), password=random_lower_string())

    # 测试 skip 参数
    r = await client.get(
        f"{settings.API_V1_STR}/users/?skip=0&limit=2",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    result = r.json()
    assert len(result["data"]) == 2

    # 测试 skip 不同值
    r2 = await client.get(
        f"{settings.API_V1_STR}/users/?skip=2&limit=2",
        headers=superuser_token_headers,
    )
    assert r2.status_code == 200
    result2 = r2.json()
    # 确保不同的 skip 返回不同的用户
    if result["data"] and result2["data"]:
        assert result["data"][0]["id"] != result2["data"][0]["id"]


async def test_get_users_normal_user_forbidden(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    """测试普通用户无法获取用户列表"""
    r = await client.get(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403


async def test_get_user_not_found(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """测试获取不存在的用户"""
    r = await client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


async def test_create_user_with_full_details(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    """测试创建包含完整信息的用户"""
    data = {
        "email": random_email(),
        "password": random_lower_string(),
        "full_name": "Test Full Name",
        "is_active": True,
        "is_superuser": False,
    }
    r = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == data["email"]
    assert created_user["full_name"] == data["full_name"]
    assert created_user["is_active"] == data["is_active"]
    assert created_user["is_superuser"] == data["is_superuser"]


async def test_update_user_all_fields(
    client: AsyncClient, superuser_token_headers: dict[str, str], db: AsyncSession
) -> None:
    """测试更新用户所有字段"""
    user = await create_test_user(
        db, email=random_email(), password=random_lower_string()
    )
    new_email = random_email()
    new_full_name = "New Full Name"
    data = {
        "email": new_email,
        "full_name": new_full_name,
        "is_active": False,
    }
    r = await client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["email"] == new_email
    assert updated["full_name"] == new_full_name
    assert updated["is_active"] is False


async def test_register_user_minimal(client: AsyncClient, db: AsyncSession) -> None:
    """测试最小信息注册用户"""
    data = {"email": random_email(), "password": random_lower_string()}
    r = await client.post(f"{settings.API_V1_STR}/users/signup", json=data)
    assert r.status_code == 200
    created_user = r.json()
    assert created_user["email"] == data["email"]
    assert created_user["full_name"] == ""


async def test_update_user_me_same_email(
    client: AsyncClient, normal_user_token_headers: dict[str, str]
) -> None:
    """测试更新用户邮箱为当前邮箱（应该成功）"""
    r = await client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"email": settings.EMAIL_TEST_USER},
    )
    assert r.status_code == 200
    assert r.json()["email"] == settings.EMAIL_TEST_USER
