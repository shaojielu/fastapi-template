import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    CurrentActiveUserDep,
    SessionDep,
    get_current_active_superuser,
)
from app.core.security import verify_password
from app.models.user import User
from app.schemas.users import (
    Message,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services.user import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_users,
    set_user_password,
    update_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(
    session: SessionDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> UsersPublic:
    """获取用户列表"""
    users, count = await get_users(session, skip=skip, limit=limit)
    return UsersPublic(data=[UserPublic.model_validate(u) for u in users], count=count)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def create_user_route(
    user_in: UserCreate,
    session: SessionDep,
) -> User:
    """创建新用户"""
    if await get_user_by_email(session, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    return await create_user(session, user_in)


@router.post("/signup", response_model=UserPublic)
async def register_user(
    user_in: UserRegister,
    session: SessionDep,
) -> User:
    """用户注册"""
    if await get_user_by_email(session, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )
    return await create_user(session, user_in)


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentActiveUserDep) -> User:
    """获取当前用户信息"""
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    user_in: UserUpdateMe,
    current_user: CurrentActiveUserDep,
    session: SessionDep,
) -> User:
    """更新当前用户信息"""
    if (
        user_in.email
        and user_in.email != current_user.email
        and await get_user_by_email(session, user_in.email)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    return await update_user(session, current_user, user_in)


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    body: UpdatePassword,
    current_user: CurrentActiveUserDep,
    session: SessionDep,
) -> Message:
    """更新当前用户密码"""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current one",
        )
    await set_user_password(session, current_user, body.new_password)
    return Message(message="Password updated successfully")


@router.delete("/me", response_model=Message)
async def delete_user_me(
    current_user: CurrentActiveUserDep,
    session: SessionDep,
) -> Message:
    """删除当前用户"""
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )
    await delete_user(session, current_user)
    return Message(message="User deleted successfully")


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: uuid.UUID,
    current_user: CurrentActiveUserDep,
    session: SessionDep,
) -> User:
    """获取指定用户信息"""
    if current_user.id == user_id:
        return current_user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user_route(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    session: SessionDep,
) -> User:
    """更新用户信息"""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    if (
        user_in.email
        and user_in.email != user.email
        and await get_user_by_email(session, user_in.email)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    return await update_user(session, user, user_in)


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
async def delete_user_route(
    user_id: uuid.UUID,
    current_user: CurrentActiveUserDep,
    session: SessionDep,
) -> Message:
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await delete_user(session, user)
    return Message(message="User deleted successfully")
