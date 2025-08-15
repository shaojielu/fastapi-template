from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import UserServiceDep
from app.schemas import Token
from app.core.config import settings
from app.core.security import create_access_token

router = APIRouter()

@router.post("/access-token", response_model=Token)
async def login_access_token(
    user_service: UserServiceDep,
    form_data:Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Authenticate user and return access token.
    """
    try:
        user = await user_service.authenticate_user(form_data.username, form_data.password)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
            )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        )