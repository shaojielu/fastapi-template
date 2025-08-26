from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models import Base

# 1. 创建数据库引擎
db_engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=settings.DB_ECHO)

# 2. 创建一个可复用的 sessionmaker (会话工厂)
db_sessionmaker = async_sessionmaker(
    db_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    """
    异步函数，用于连接数据库并根据模型创建所有表。
    """
    async with db_engine.begin() as conn:
        # 检查表是否存在，如果不存在，则创建它们。如果表已存在，它不会做任何事情。
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    一个依赖提供函数，为每个请求创建一个新的DB会话。
    它使用全局的 db_sessionmaker 创建会话。
    """

    # 使用 sessionmaker 创建一个新的会话
    async with db_sessionmaker() as session:
        yield session
