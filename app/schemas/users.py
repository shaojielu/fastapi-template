import datetime
import uuid

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema


class Token(BaseModel):
    """登录成功后返回的令牌"""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """令牌有效负载"""

    sub: uuid.UUID | None = None


class Message(BaseModel):
    """通用消息响应"""

    message: str


class NewPassword(BaseModel):
    """重置密码时需要提供的数据"""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UserBase(BaseModel):
    """用户核心字段"""

    email: EmailStr = Field(max_length=255)
    full_name: str = Field(default="", max_length=255)
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """创建用户时需要提供的数据"""

    password: str = Field(..., min_length=8, max_length=128)


class UserRegister(BaseModel):
    """用户注册时需要提供的数据"""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(BaseModel):
    """更新用户时可选的数据"""

    email: EmailStr | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(BaseModel):
    """更新当前用户信息时需要提供的数据"""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(BaseModel):
    """更新当前用户密码时需要提供的数据"""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(UserBase, BaseSchema):
    """公开的用户信息，不包含密码"""

    id: uuid.UUID
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class UsersPublic(BaseSchema):
    """分页查询用户公开信息时返回的数据"""

    data: list[UserPublic]
    count: int


class PrivateUserCreate(BaseModel):
    """内部 API 创建用户时需要提供的数据"""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(max_length=255)
