from fastapi import APIRouter

from app.api.deps import SessionDep
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.users import PrivateUserCreate, UserPublic

router = APIRouter(prefix="/private", tags=["private"])


@router.post("/users/", response_model=UserPublic)
async def create_user(user_in: PrivateUserCreate, session: SessionDep) -> User:
    """创建新用户（内部 API）"""
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    await session.flush()

    return user
