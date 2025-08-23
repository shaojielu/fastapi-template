# conftest.py

from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient  # 导入 AsyncClient 和 ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.api.deps import get_db
from app.api.main import app
from app.repositories import UserRepositorie
from app.services.user_service import UserService
from app.models import Base, User
from app.schemas import UserCreate
from app.core.config import settings, Settings


pytestmark = pytest.mark.anyio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_db_engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(
    test_db_engine, class_=AsyncSession, expire_on_commit=False
)


# --- Fixture 定义 ---
@pytest.fixture
def anyio_backend():
    """
    强制所有 anyio 测试都使用 asyncio 后端。
    这是因为 SQLAlchemy 的异步支持是基于 asyncio 构建的。
    """
    return "asyncio"


@pytest.fixture(scope="function")
async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def user_service(get_test_db: AsyncSession) -> UserService:
    user_repo = UserRepositorie(session=get_test_db)
    user_service = UserService(user_repo=user_repo, session=get_test_db)
    return user_service


@pytest.fixture(scope="function")
async def existing_user(user_service: UserService) -> User:
    user_create_data = UserCreate(
        full_name="Existing User",
        email="existing@example.com",
        password="a-plain-password",
    )
    created_user = await user_service.create_user(user_create_data)
    return created_user


@pytest.fixture(scope="function")
async def another_user(user_service: UserService) -> User:
    user_create_data = UserCreate(
        full_name="Another Test User",
        email="another@example.com",
        password="a-plain-password-for-another",
    )
    created_user = await user_service.create_user(user_create_data)
    return created_user


@pytest.fixture(scope="function")
async def client(get_test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    提供一个 httpx.AsyncClient，用于进行异步 API 测试。
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield get_test_db

    app.dependency_overrides[get_db] = override_get_db

    # 使用 AsyncClient 和 ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def auth_headers(client: AsyncClient, existing_user: User) -> dict[str, str]:
    """
    Fixture，用于登录 existing_user 并返回认证头。
    现在是异步的，并使用 AsyncClient。
    """
    login_data = {
        "username": existing_user.email,
        "password": "a-plain-password",
    }

    login_url = f"{settings.API_V1_STR}/login/access-token"
    # 使用 await 进行异步请求
    response = await client.post(login_url, data=login_data)

    if response.status_code != 200:
        raise Exception(f"Failed to log in user: {response.json()}")

    token_data = response.json()
    access_token = token_data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


class MockSettings:
    S3_BUCKET_NAME = "test-bucket"
    S3_ACCESS_KEY = "test-access-key"
    S3_SECRET_KEY = "test-secret-key"
    S3_REGION_NAME = "us-east-1"
    S3_ENDPOINT_URL = "http://localhost:9000"

    TENCENT_COS_BUCKET = "test-cos-bucket-123456789"
    TENCENT_COS_REGION = "ap-guangzhou"
    TENCENT_COS_SECRET_ID = "test-cos-secret-id"
    TENCENT_COS_SECRET_KEY = "test-cos-secret-key"

    STORAGE_PROVIDER = "s3"  # 默认提供商


@pytest.fixture
def mock_settings() -> MockSettings:
    """提供一个用于测试的模拟配置对象。"""
    return MockSettings()
