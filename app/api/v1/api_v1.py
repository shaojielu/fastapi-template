from fastapi import APIRouter

from app.api.v1.endpoints import (
    login, 
    users,
)

api_router = APIRouter()

api_router.include_router(login.router,prefix="/login",tags=["用户验证"])
api_router.include_router(users.router,prefix="/users", tags=["用户"])