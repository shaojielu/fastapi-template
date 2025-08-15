# tests/services/test_user_service.py

import pytest
import uuid
from app.services.user_service import UserService
from app.schemas import UserCreate, UserUpdate
from app.core.security import verify_password # 导入密码验证函数以进行断言
from tests.conftest import existing_user

# 使用此标记，pytest-asyncio 插件会自动处理文件中的所有异步测试函数
pytestmark = pytest.mark.asyncio


# --- 测试 create_user 方法 ---
async def test_create_user_success(user_service: UserService):
    """
    测试场景：成功创建一个新用户。
    """
    # 准备 (Arrange)
    user_in = UserCreate(
        full_name="New Test User",
        email="new.user@example.com",
        password="a-strong-password-123"
    )

    # 执行 (Act)
    created_user = await user_service.create_user(user_in)

    # 断言 (Assert)
    assert created_user is not None
    assert created_user.id is not None
    assert created_user.email == user_in.email
    assert created_user.full_name == user_in.full_name
    assert created_user.is_active is True
    # 验证密码确实被哈希了
    assert await verify_password(user_in.password, created_user.hashed_password)


async def test_create_user_with_duplicate_email_raises_error(user_service: UserService, existing_user):
    """
    测试场景：当使用一个已存在的邮箱创建用户时，应抛出 ValueError。
    """
    # 准备 (Arrange)
    user_in_duplicate = UserCreate(
        full_name="Another User",
        email=existing_user.email,  # 使用与 existing_user 相同的邮箱
        password="another_password"
    )

    # 执行并断言 (Act & Assert)
    with pytest.raises(ValueError, match="Email already registered"):
        await user_service.create_user(user_in_duplicate)


# --- 测试 get_user_by_id 方法 ---
async def test_get_user_by_id_success(user_service: UserService, existing_user):
    """
    测试场景：根据 ID 成功获取一个用户。
    """
    # 执行 (Act)
    found_user = await user_service.get_user_by_id(existing_user.id)

    # 断言 (Assert)
    assert found_user is not None
    assert found_user.id == existing_user.id
    assert found_user.email == existing_user.email


async def test_get_user_by_id_not_found_returns_none(user_service: UserService):
    """
    测试场景：使用一个不存在的 UUID 获取用户时，应返回 None。
    """
    # 执行 (Act)
    found_user = await user_service.get_user_by_id(uuid.uuid4())

    # 断言 (Assert)
    assert found_user is None


# --- 测试 update_user 方法 ---
async def test_update_user_success(user_service: UserService, existing_user):
    """
    测试场景：成功更新用户的姓名和密码。
    """
    # 准备 (Arrange)
    update_data = UserUpdate(
        full_name="Updated Name",
        email="second@example.com",
        password="new-strong-password"
    )

    # 执行 (Act)
    updated_user = await user_service.update_user(existing_user.id, update_data)

    # 断言 (Assert)
    assert updated_user.id == existing_user.id
    assert updated_user.full_name == "Updated Name"
    assert updated_user.email == existing_user.email  # 邮箱应保持不变
    assert await verify_password("new-strong-password", updated_user.hashed_password)


async def test_update_user_not_found_raises_error(user_service: UserService):
    """
    测试场景：尝试更新一个不存在的用户时，应抛出 ValueError。
    """
    # 准备 (Arrange)
    update_data = UserUpdate(full_name="any name",email="second@example.com")

    # 执行并断言 (Act & Assert)
    with pytest.raises(ValueError, match="User not found"):
        await user_service.update_user(uuid.uuid4(), update_data)


async def test_update_user_to_duplicate_email_raises_error(user_service: UserService, existing_user):
    """
    测试场景：尝试将一个用户的邮箱更新为另一个已存在的邮箱时，应抛出 ValueError。
    """
    # 准备 (Arrange)：创建第二个用户
    second_user_in = UserCreate(full_name="Second User", email="second@example.com", password="password123")
    second_user = await user_service.create_user(second_user_in)

    # 准备更新数据，试图将 second_user 的邮箱改成 existing_user 的邮箱
    update_data = UserUpdate(full_name="Second User",email=existing_user.email)

    # 执行并断言 (Act & Assert)
    with pytest.raises(ValueError, match="This email is already registered to another user."):
        await user_service.update_user(second_user.id, update_data)


# --- 测试 authenticate_user 方法 ---
async def test_authenticate_user_success(user_service: UserService, existing_user):
    """
    测试场景：使用正确的邮箱和密码成功认证用户。
    """
    # 准备 (Arrange)
    plain_password = "a-plain-password"  # 这是创建 existing_user 时使用的密码

    # 执行 (Act)
    authenticated_user = await user_service.authenticate_user(existing_user.email, plain_password)

    # 断言 (Assert)
    assert authenticated_user is not None
    assert authenticated_user.email == existing_user.email


async def test_authenticate_user_wrong_password_returns_none(user_service: UserService, existing_user):
    """
    测试场景：使用错误的密码进行认证时，应返回 None。
    """
    # 执行 (Act)
    result = await user_service.authenticate_user(existing_user.email, "wrong-password")

    # 断言 (Assert)
    assert result is None


async def test_authenticate_user_nonexistent_email_returns_none(user_service: UserService):
    """
    测试场景：使用不存在的邮箱进行认证时，应返回 None。
    """
    # 执行 (Act)
    result = await user_service.authenticate_user("no-one@example.com", "any-password")

    # 断言 (Assert)
    assert result is None