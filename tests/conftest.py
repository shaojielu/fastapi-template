import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio  # 导入 pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from app.models import Base, User
from app.repositories.user_repo import UserRepositorie
from app.services.user_service import UserService
from app.schemas import UserCreate

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_db_engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        await session.begin()
        yield session
        await session.rollback()

    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def existing_user(user_service: UserService) -> User:
    user_create_data = UserCreate(
        full_name="Existing User",
        email="existing@example.com",
        password="a-plain-password"
    )
    created_user = await user_service.create_user(user_create_data)
    return created_user

@pytest.fixture(scope="function")
def user_service(db_session: AsyncSession) -> UserService:
    """
    一个用于创建和提供 UserService 实例的 Fixture。
    它依赖于 db_session fixture 来获取数据库会话。
    """
    # 1. 创建 Repository 实例
    user_repo = UserRepositorie(session=db_session)
    
    # 2. 创建 Service 实例，并传入 Repository
    service = UserService(user_repo=user_repo,session=db_session)
    
    return service