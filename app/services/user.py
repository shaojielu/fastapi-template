import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.users import UserCreate, UserRegister, UserUpdate, UserUpdateMe


async def create_user(
    session: AsyncSession, user_in: UserCreate | UserRegister
) -> User:
    """创建用户"""
    user = User(
        email=user_in.email,
        full_name=getattr(user_in, "full_name", None) or "",
        hashed_password=get_password_hash(user_in.password),
        is_active=getattr(user_in, "is_active", True),
        is_superuser=getattr(user_in, "is_superuser", False),
    )
    session.add(user)
    await session.flush()
    return user


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    """根据 ID 获取用户"""
    return await session.get(User, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """根据邮箱获取用户"""
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_users(
    session: AsyncSession, *, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    """获取用户列表"""
    count_stmt = select(func.count()).select_from(User)
    total = await session.execute(count_stmt)
    count = total.scalar() or 0

    stmt = select(User).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all()), count


async def update_user(
    session: AsyncSession, user: User, user_in: UserUpdate | UserUpdateMe
) -> User:
    """更新用户"""
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(user, key, value)
    await session.flush()
    await session.refresh(user)
    return user


async def set_user_password(
    session: AsyncSession, user: User, new_password: str
) -> None:
    """设置密码"""
    user.hashed_password = get_password_hash(new_password)
    await session.flush()


async def delete_user(session: AsyncSession, user: User) -> None:
    """删除用户"""
    await session.delete(user)
    await session.flush()


async def authenticate(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user
