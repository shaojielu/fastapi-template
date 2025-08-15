import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.repositories.user_repo import UserRepositorie

class UserService:
    def __init__(self, user_repo: UserRepositorie, session: AsyncSession):
        self.user_repo = user_repo
        self.session = session # 仍然需要session来控制事务

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """根据用户ID获取用户。"""
        return await self.user_repo.get_by_id(user_id)

    async def create_user(self, user_create: UserCreate) -> User:
        """
        创建新用户，并处理所有业务逻辑。
        """
        # 业务规则：检查邮箱是否已注册
        if await self.user_repo.get_by_email(user_create.email):
            raise ValueError("Email already registered") # 使用更具体的异常类型
        
        # 业务安全逻辑：哈希密码
        hashed_password = await get_password_hash(user_create.password)
        
        # 创建数据库模型对象
        new_user = User(
            full_name=user_create.full_name,
            email=user_create.email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        self.user_repo.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def update_user(self, user_id: uuid.UUID, user_update: UserUpdate) -> User:
        """更新用户信息。"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        update_data = user_update.model_dump(exclude_unset=True)

        # 业务规则：检查新邮箱是否已被其他用户注册
        if "email" in update_data and update_data["email"] != user.email:
            existing_user = await self.user_repo.get_by_email(update_data["email"])
            if existing_user and existing_user.id != user_id:
                raise ValueError("This email is already registered to another user.")
        
        for key, value in update_data.items():
            if key == "password" and value is not None:
                # 业务安全逻辑：哈希新密码
                setattr(user, "hashed_password", await get_password_hash(value))
            else:
                setattr(user, key, value)
        
        # self.user_repo.update(user) # 标记更新 (可选)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """认证用户。"""
        db_user = await self.user_repo.get_by_email(email)
        
        if not db_user or not await verify_password(password, db_user.hashed_password):
            return None # 认证失败返回 None，让上层处理异常或响应
        
        return db_user