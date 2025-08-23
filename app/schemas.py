import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BaseSchema(BaseModel):
    """
    所有 Schema 的基类，自动启用 ORM 模式 (from_attributes)。
    """

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# class TokenPayload(BaseModel):
#     sub: Optional[str] = None


class TokenPayload(BaseModel):
    sub: uuid.UUID | None = None


# 用户
class UserBase(BaseModel):
    """用户核心字段"""

    full_name: str
    email: EmailStr = Field(..., description="用户邮箱，作为登录标识。")


class UserCreate(UserBase):
    """创建用户时需要提供的数据"""

    password: str = Field(..., min_length=8, description="用户密码，最少8位。")


class UserUpdate(BaseModel):
    """更新用户时可选的数据"""

    full_name: str | None = None
    email: EmailStr | None = Field(None, description="用户邮箱，作为登录标识。")
    password: str | None = Field(None, min_length=8, description="新的用户密码。")
    is_active: bool | None = Field(None, description="是否激活用户。")
    updated_at: datetime | None = Field(None)


class UserPublic(UserBase, BaseSchema):
    """公开的用户信息，不包含密码"""

    id: uuid.UUID
    is_active: bool
