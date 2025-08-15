from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.core.db import get_db
from app.core.config import settings
from app.models import User
from app.schemas import TokenPayload
from app.providers.storage import BaseStorageService,StorageFactory
from app.repositories.user_repo import UserRepositorie
from app.services.user_service import UserService



DBSessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_storage_service() -> BaseStorageService:
    return StorageFactory.get_service("cos",settings)
StorageServiceDep = Annotated[BaseStorageService, Depends(get_storage_service)]


def get_user_repo(db: DBSessionDep) -> UserRepositorie:
    return UserRepositorie(session=db)
UserRepositorieDep = Annotated[UserRepositorie,Depends(get_user_repo)]

def get_user_service(db: DBSessionDep,user_repo:UserRepositorieDep) -> UserService:
    return UserService(session=db,user_repo=user_repo)
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(user_service:UserServiceDep,token:TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await user_service.get_user_by_id(token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUserDep) -> User:
    if current_user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]