import uuid
from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User

class BaseRepositorie(ABC):
    pass

class UserRepositorie:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """根据ID获取用户。"""
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱获取用户。"""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def add(self, user: User) -> None:
        """将用户对象添加到session中，准备创建。"""
        self.session.add(user)

    def update(self, user: User) -> User:
        """
        标记一个用户为已修改。
        注意：在异步会话中，对象通常会自动跟踪更改，
        此方法可以为空，或用于更复杂逻辑。
        """
        # SQLAlchemy 的 session 会自动跟踪对象变化，所以通常不需要显式调用 update
        return user

    async def delete_by_id(self, user_id: uuid.UUID) -> None:
        """根据ID删除用户。"""
        user = await self.get_by_id(user_id)
        if user:
            await self.session.delete(user)