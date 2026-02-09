from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session, engine
from app.initial_data import init_db
from app.main import app
from app.models.base import Base
from app.models.user import User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """为整个测试会话提供一个 asyncio 后端。"""
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def setup_db() -> None:
    """创建数据库表（会话级别，仅执行一次）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession]:
    """
    获取数据库会话（函数级别）。
    每个测试函数获得独立的数据库会话，测试结束后清理非超级用户数据。
    """
    async with async_session() as session:
        # 确保超级用户存在
        await init_db(session)
        yield session
        # 回滚未提交的更改
        await session.rollback()
        # 只清理非超级用户的测试数据，保留超级用户以提高效率
        await session.execute(
            delete(User).where(User.email != settings.FIRST_SUPERUSER)
        )
        await session.commit()


@pytest.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """获取测试客户端（函数级别），依赖db确保数据库已初始化"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture(scope="function")
async def superuser_token_headers(
    client: AsyncClient, db: AsyncSession
) -> dict[str, str]:
    """获取超级用户认证头（函数级别）"""
    return await get_superuser_token_headers(client)


@pytest.fixture(scope="function")
async def normal_user_token_headers(
    client: AsyncClient, db: AsyncSession
) -> dict[str, str]:
    """获取普通用户认证头（函数级别）"""
    return await authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
