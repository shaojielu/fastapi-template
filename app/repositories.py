import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base, User  # 假设您的模型都继承自一个共同的 Base


class BaseRepository[ModelType: Base]:
    """一个通用的、与具体模型无关的 Repository 基类。"""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """
        初始化 Repository。

        :param model: SQLAlchemy 模型类。
        :param session: SQLAlchemy 的 AsyncSession 实例。
        """
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: uuid.UUID | int) -> ModelType | None:
        """根据主键 ID 获取一个实体。"""
        return await self.session.get(self.model, entity_id)

    def add(self, entity: ModelType) -> None:
        """
        将一个实体对象添加到 session 中，准备创建。
        """
        self.session.add(entity)

    async def delete(self, entity: ModelType) -> None:
        """
        从 session 中删除一个实体。
        """
        await self.session.delete(entity)

    async def delete_by_id(self, entity_id: uuid.UUID | int) -> bool:
        """
        根据主键 ID 删除一个实体。

        :return: 如果找到并删除了实体，则返回 True，否则返回 False。
        """
        entity = await self.get_by_id(entity_id)
        if entity:
            await self.session.delete(entity)
            return True
        return False


class UserRepositorie(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        # 初始化父类，并传入 User 模型
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """
        根据邮箱获取用户（这是 UserRepositorie 特有的方法）。
        """
        query = select(self.model).where(self.model.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # get_by_id, add 和 delete_by_id 方法现在都由 BaseRepository 继承而来
    # 无需在此重复实现

    def update(self, user: User) -> User:
        """
        标记一个用户为已修改。
        注意：在异步会话中，对象通常会自动跟踪更改，
        此方法可以为空，或用于更复杂逻辑。
        """
        # SQLAlchemy 的 session 会自动跟踪对象变化，所以通常不需要显式调用 update
        # 这个方法可以保留，以备将来需要添加特殊逻辑
        return user
