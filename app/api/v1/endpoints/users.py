import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import UserServiceDep, CurrentActiveUserDep
from app.schemas import UserCreate, UserPublic, UserUpdate

router = APIRouter()

@router.post("/", response_model=UserPublic)
async def create_user(
    user_create: UserCreate,
    user_service: UserServiceDep,
):
    """
    创建新用户。
    """
    try:
        new_user = await user_service.create_user(user_create=user_create)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.get("/me", response_model=UserPublic)
async def read_user_me(
    current_user: CurrentActiveUserDep,
):
    """
    获取当前用户信息。
    """
    return current_user

@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_service: UserServiceDep,
    current_user: CurrentActiveUserDep,
    user_id: uuid.UUID,
    user_update: UserUpdate,
):
    """
    更新用户信息。
    """
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    
    try:
        updated_user = await user_service.update_user(user_id=user_id, user_update=user_update)
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="更新用户异常")