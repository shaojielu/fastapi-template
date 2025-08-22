from typing import AsyncGenerator

import pytest
import pytest_asyncio  # 导入 pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.api.main import app
from app.repositories import UserRepositorie
from app.services.user_service import UserService
from app.models import Base,User
from app.schemas import UserCreate
from app.core.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_db_engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)

# --- Fixture 定义 ---
@pytest_asyncio.fixture(scope="function")
async def get_test_db() -> AsyncGenerator[AsyncSession, None]:

    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session

    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def user_service(get_test_db: AsyncSession) -> UserService:
    """
    一个用于创建和提供 UserService 实例的 Fixture。
    """
    # 1. 创建 Repository 实例
    user_repo = UserRepositorie(session=get_test_db)
    # 2. 创建 Service 实例，并传入 Repository
    user_service = UserService(user_repo=user_repo,session=get_test_db)
    
    return user_service

@pytest_asyncio.fixture(scope="function")
async def existing_user(user_service: UserService) -> User:
    user_create_data = UserCreate(
        full_name="Existing User",
        email="existing@example.com",
        password="a-plain-password"
    )
    created_user = await user_service.create_user(user_create_data)
    return created_user

@pytest_asyncio.fixture(scope="function")
async def another_user(user_service: UserService) -> User:
    """
    Fixture for creating a second, distinct user for permission tests.
    """
    user_create_data = UserCreate(
        full_name="Another Test User",
        email="another@example.com",
        password="a-plain-password-for-another"
    )
    created_user = await user_service.create_user(user_create_data)
    return created_user

@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: TestClient, existing_user: User) -> dict[str, str]:
    """
    Fixture to log in the existing_user and return authentication headers.
    """
    login_data = {
        "username": existing_user.email,
        "password": "a-plain-password", # 必须与 existing_user 的密码匹配
    }
    
    login_url = f"{settings.API_V1_STR}/login/access-token"
    response = client.post(login_url, data=login_data)
    
    if response.status_code != 200:
        raise Exception(f"Failed to log in user: {response.json()}")
        
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="function")
async def client(get_test_db: AsyncSession) -> AsyncGenerator[TestClient, None]:

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield get_test_db

    # app.dependency_overrides[get_db] = lambda:get_test_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()