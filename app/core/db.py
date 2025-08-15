from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker,create_async_engine

from app.core.config import settings

# 1. 创建数据库引擎
db_engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=settings.DB_ECHO)

# 2. 创建一个可复用的 sessionmaker (会话工厂)
db_sessionmaker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    一个依赖提供函数，为每个请求创建一个新的DB会话。
    它使用全局的 db_sessionmaker 创建会话。
    """
    
    # 使用 sessionmaker 创建一个新的会话
    async with db_sessionmaker() as session:
            yield session